import os
from flask import Flask, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from flask_session import Session
from models import db, Teacher, Course, Student, Attendance, MaterialTarget, StudentMetric, QuestionPaper
from dotenv import load_dotenv
import google.oauth2.credentials
import io
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request
from openai import OpenAI
from sqlalchemy import text
from datetime import datetime
from ai_checker import handle_upload, analyze_text

# 1. Force HTTP for local testing (No HTTPS needed)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def _clean_env(value):
    if value is None:
        return None
    return value.strip().strip('"').strip("'")

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super_secret_dev_key')
CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://127.0.0.1:5173"])

# SQLite Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///classops.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Server-side sessions to avoid oversized cookie payloads for OAuth tokens
session_dir = os.path.join(app.instance_path, "sessions")
os.makedirs(session_dir, exist_ok=True)
app.config.update(
    SESSION_TYPE="filesystem",
    SESSION_FILE_DIR=session_dir,
    SESSION_PERMANENT=False,
    SESSION_USE_SIGNER=True,
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=False
)
Session(app)
db.init_app(app)

# ==========================================
# API KEYS (To be filled in .env file)
# ==========================================
OPENAI_API_KEY = _clean_env(os.getenv('OPENAI_API_KEY'))
CLIENT_SECRETS_FILE = "client_secret.json" # Download from Google Cloud Console
SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly', 
          'https://www.googleapis.com/auth/classroom.rosters.readonly']
GOOGLE_REDIRECT_URI = "http://localhost:5000/api/auth/google/callback"

# Initialize DB

def ensure_attendance_schema():
    try:
        cols = db.session.execute(text("PRAGMA table_info(attendance)")).fetchall()
        if not any(col[1] == "course_id" for col in cols):
            db.session.execute(text("ALTER TABLE attendance ADD COLUMN course_id INTEGER"))
            db.session.commit()
    except Exception as exc:
        app.logger.exception("Schema check failed: %s", exc)

with app.app_context():
    db.create_all()
    ensure_attendance_schema()

def _build_credentials(credentials_dict=None):
    if credentials_dict is None:
        credentials_dict = session.get('credentials')
    if not credentials_dict:
        return None
    creds = google.oauth2.credentials.Credentials(**credentials_dict)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        session['credentials'] = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
    return creds


def get_classroom_service(credentials_dict=None):
    creds = _build_credentials(credentials_dict)
    if not creds:
        return None
    return build('classroom', 'v1', credentials=creds)

def get_drive_service(credentials_dict=None):
    creds = _build_credentials(credentials_dict)
    if not creds:
        return None
    return build('drive', 'v3', credentials=creds)


def _missing_scopes(creds):
    creds_scopes = set(creds.scopes or [])
    return [s for s in SCOPES if s not in creds_scopes]


def _download_drive_file(drive_service, file_id):
    try:
        meta = drive_service.files().get(fileId=file_id, fields="id,name,mimeType").execute()
        mime_type = meta.get('mimeType')
        name = meta.get('name') or 'submission'

        if mime_type and mime_type.startswith('application/vnd.google-apps.'):
            if mime_type == 'application/vnd.google-apps.document':
                export_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                filename = f"{name}.docx"
            else:
                export_mime = 'application/pdf'
                filename = f"{name}.pdf"
            request = drive_service.files().export_media(fileId=file_id, mimeType=export_mime)
        else:
            request = drive_service.files().get_media(fileId=file_id)
            filename = name
            if not os.path.splitext(filename)[1]:
                if mime_type == 'application/pdf':
                    filename += '.pdf'
                elif mime_type in ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword'):
                    filename += '.docx'

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return fh.getvalue(), filename, None
    except Exception as exc:
        return None, None, str(exc)

def sync_classroom_data(credentials_dict=None):
    service = get_classroom_service(credentials_dict)
    if not service:
        raise ValueError("Missing Google credentials. Please authenticate first.")

    results = service.courses().list(pageSize=10).execute()
    courses_data = results.get('courses', [])

    # Ensure at least one teacher exists
    teacher = Teacher.query.get(1)
    if not teacher:
        teacher = Teacher(id=1, email="admin@classops.local", name="Admin Teacher")
        db.session.add(teacher)
        db.session.commit()

    for c in courses_data:
        if not Course.query.filter_by(google_course_id=c['id']).first():
            new_course = Course(google_course_id=c['id'], name=c['name'], teacher_id=teacher.id)
            db.session.add(new_course)
    db.session.commit()
    return courses_data

def serialize_course(course):
    return {
        "id": course.id,
        "name": course.name,
        "google_course_id": course.google_course_id
    }
# ==========================================
# 1. GOOGLE CLASSROOM INTEGRATION
# ==========================================
@app.route('/api/auth/google')
def google_auth():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        code_challenge_method='S256'
    )
    session['state'] = state
    session['code_verifier'] = flow.code_verifier
    return redirect(authorization_url)

@app.route('/api/auth/google/url')
def google_auth_url():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        code_challenge_method='S256'
    )
    session['state'] = state
    session['code_verifier'] = flow.code_verifier
    return jsonify({"auth_url": authorization_url})

@app.route('/api/auth/google/callback')
def google_auth_callback():
    state = session.get('state')
    code_verifier = session.get('code_verifier')
    if not state or not code_verifier:
        return jsonify({"error": "Missing OAuth session. Please start auth again."}), 400

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    flow.fetch_token(authorization_response=request.url, code_verifier=code_verifier)

    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    try:
        sync_classroom_data(session['credentials'])
    except Exception as exc:
        app.logger.exception("Classroom sync failed: %s", exc)
    return redirect('http://localhost:5173/') # Redirect to React App

@app.route('/api/classroom/sync')
def sync_classroom():
    if 'credentials' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    sync_classroom_data(session['credentials'])
    courses = Course.query.all()
    return jsonify({"message": "Classroom synced successfully", "courses": [serialize_course(c) for c in courses]})

@app.route('/api/courses', methods=['GET'])
def list_courses():
    courses = Course.query.all()
    return jsonify([serialize_course(c) for c in courses]), 200

# ==========================================
# Classroom Coursework & Submissions
# ==========================================
@app.route('/api/classroom/courses/<int:course_id>/coursework', methods=['GET'])
def list_coursework(course_id):
    if 'credentials' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    course = Course.query.get(course_id)
    if not course:
        course = Course.query.filter_by(google_course_id=str(course_id)).first()
    if not course or not course.google_course_id:
        return jsonify({"error": "Course not linked to Google Classroom"}), 400

    creds = _build_credentials()
    if not creds:
        return jsonify({"error": "Not authenticated"}), 401
    missing = _missing_scopes(creds)
    if missing:
        return jsonify({"error": "Missing Google Classroom/Drive permissions. Please re-auth.", "reauth": True}), 403

    service = get_classroom_service()
    if not service:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        items = []
        page_token = None
        while True:
            resp = service.courses().courseWork().list(
                courseId=course.google_course_id,
                pageToken=page_token,
                pageSize=50
            ).execute()
            items.extend(resp.get('courseWork', []))
            page_token = resp.get('nextPageToken')
            if not page_token:
                break

        payload = [
            {
                "id": item.get('id'),
                "title": item.get('title'),
                "state": item.get('state'),
                "maxPoints": item.get('maxPoints'),
                "dueDate": item.get('dueDate')
            }
            for item in items
        ]
        return jsonify(payload), 200
    except Exception as exc:
        app.logger.exception("Failed to list coursework: %s", exc)
        return jsonify({"error": "Failed to load assignments"}), 500


@app.route('/api/classroom/courses/<int:course_id>/coursework/<coursework_id>/plagiarism', methods=['POST'])
def analyze_coursework_plagiarism(course_id, coursework_id):
    if 'credentials' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    course = Course.query.get(course_id)
    if not course:
        course = Course.query.filter_by(google_course_id=str(course_id)).first()
    if not course or not course.google_course_id:
        return jsonify({"error": "Course not linked to Google Classroom"}), 400

    creds = _build_credentials()
    if not creds:
        return jsonify({"error": "Not authenticated"}), 401
    missing = _missing_scopes(creds)
    if missing:
        return jsonify({"error": "Missing Google Classroom/Drive permissions. Please re-auth.", "reauth": True}), 403

    classroom = get_classroom_service()
    drive = get_drive_service()
    if not classroom or not drive:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        submissions = []
        page_token = None
        while True:
            resp = classroom.courses().courseWork().studentSubmissions().list(
                courseId=course.google_course_id,
                courseWorkId=coursework_id,
                pageToken=page_token,
                pageSize=50
            ).execute()
            submissions.extend(resp.get('studentSubmissions', []))
            page_token = resp.get('nextPageToken')
            if not page_token:
                break

        results = []
        for sub in submissions:
            if sub.get('state') not in ('TURNED_IN', 'RETURNED'):
                continue

            attachments = sub.get('assignmentSubmission', {}).get('attachments', [])
            percent_values = []
            analyzed_files = 0
            skipped_files = 0

            for att in attachments:
                drive_file = att.get('driveFile')
                if not drive_file:
                    skipped_files += 1
                    continue

                file_id = drive_file.get('id') or drive_file.get('driveFile', {}).get('id')
                if not file_id:
                    skipped_files += 1
                    continue

                file_bytes, filename, err = _download_drive_file(drive, file_id)
                if not file_bytes:
                    skipped_files += 1
                    continue

                analyzed_files += 1
                analysis = handle_upload(file_bytes, filename)
                data = analysis.get('data', {})
                percentage = data.get('percentage')
                try:
                    if percentage is not None:
                        percent_values.append(float(percentage))
                except Exception:
                    pass

                # limit to first supported file per submission
                break

            user_id = sub.get('userId')
            student = Student.query.filter_by(roll_number=str(user_id), course_id=course.id).first()
            student_name = student.name if student else str(user_id)

            results.append({
                "student_id": user_id,
                "student_name": student_name,
                "percentage": max(percent_values) if percent_values else None,
                "status": sub.get('state'),
                "analyzed_files": analyzed_files,
                "skipped_files": skipped_files
            })

        return jsonify({"results": results, "total": len(results)}), 200
    except Exception as exc:
        app.logger.exception("Plagiarism check failed: %s", exc)
        return jsonify({"error": "Failed to analyze submissions"}), 500
# ==========================================
# 2. AI CONTENT DETECTION (RapidAPI)
# ==========================================
@app.route('/api/assignments/check', methods=['POST'])
def check_plagiarism():
    if 'file' in request.files:
        file = request.files['file']
        if not file or not file.filename:
            return jsonify({"success": False, "error": "No file uploaded"}), 400
        result = handle_upload(file)
        return jsonify(result), 200

    data = request.get_json(silent=True) or {}
    text_to_check = data.get('text')
    if text_to_check:
        result = analyze_text(text_to_check)
        return jsonify(result), 200

    return jsonify({"success": False, "error": "Provide a file upload or a text field."}), 400

# ==========================================
# 3. QUESTION PAPER CREATION (BLOOM'S TAXONOMY)
# ==========================================

def _build_bloom_template(topic, difficulty, syllabus_items=None):
    syllabus_items = syllabus_items or []
    header = [
        f"Question Paper: {topic}",
        f"Difficulty: {difficulty}",
    ]
    if syllabus_items:
        header.append("Syllabus Targets: " + ", ".join(syllabus_items))

    lines = header + [
        "",
        "Part A (Remember & Understand) - 5 short questions",
        f"1. Define the core concepts of {topic}.",
        f"2. List key components or terminology used in {topic}.",
        f"3. Explain the basic workflow or life cycle in {topic}.",
        f"4. Give two real-world examples where {topic} is applied.",
        f"5. Compare two foundational approaches within {topic}.",
        "",
        "Part B (Apply & Analyze) - 3 medium questions",
        f"6. Apply {topic} principles to solve a practical scenario of your choice.",
        f"7. Analyze a case study and identify strengths and weaknesses related to {topic}.",
        f"8. Solve a problem by selecting appropriate methods from {topic} and justify your choice.",
        "",
        "Part C (Evaluate & Create) - 2 essay questions",
        f"9. Evaluate modern trends in {topic} and argue their impact on industry.",
        f"10. Propose an improved system or model using {topic} concepts, including design rationale.",
    ]
    return "\n".join(lines)


def _generate_question_paper_content(topic, difficulty, syllabus_items=None):
    if OPENAI_API_KEY:
        prompt_parts = [
            f"Generate a university-level question paper on '{topic}' with a '{difficulty}' difficulty.",
            "Format it strictly according to Bloom's Taxonomy:",
            "Part A (Remember & Understand) - 5 short questions",
            "Part B (Apply & Analyze) - 3 medium questions",
            "Part C (Evaluate & Create) - 2 essay questions",
        ]
        if syllabus_items:
            prompt_parts.append("Align questions to these syllabus targets: " + ", ".join(syllabus_items))
        prompt = "\n".join(prompt_parts)

        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a university professor."},
                    {"role": "user", "content": prompt}
                ]
            )
            if response.choices:
                content = response.choices[0].message.content
                if content:
                    return content, "openai"
        except Exception as exc:
            app.logger.exception("Question paper generation failed: %s", exc)

    return _build_bloom_template(topic, difficulty, syllabus_items), "template"


@app.route('/api/question-paper/generate', methods=['POST'])
def generate_question_paper():
    data = request.get_json(silent=True) or {}
    topic = (data.get('topic') or "").strip()
    difficulty = (data.get('difficulty') or 'Medium').strip()
    course_id = data.get('course_id')
    use_cache = data.get('use_cache', True)

    if not topic:
        return jsonify({"question_paper": "Please provide a topic to generate a question paper."}), 200

    if use_cache:
        cached = QuestionPaper.query.filter_by(topic=topic, difficulty=difficulty).order_by(QuestionPaper.created_at.desc()).first()
        if cached:
            return jsonify({"question_paper": cached.content, "source": "cache", "id": cached.id}), 200

    syllabus_items = []
    if course_id:
        targets = MaterialTarget.query.filter_by(course_id=course_id).order_by(MaterialTarget.target_date.asc()).all()
        syllabus_items = [t.topic for t in targets]

    content, source = _generate_question_paper_content(topic, difficulty, syllabus_items)

    try:
        qp = QuestionPaper(topic=topic, difficulty=difficulty, content=content)
        db.session.add(qp)
        db.session.commit()
        qp_id = qp.id
    except Exception as exc:
        db.session.rollback()
        app.logger.exception("Failed to save question paper: %s", exc)
        qp_id = None

    return jsonify({"question_paper": content, "source": source, "id": qp_id}), 200

# ==========================================
# 4. MATERIAL TARGET COMPLETION
# ==========================================
@app.route('/api/targets', methods=['GET', 'POST'])
def manage_targets():
    if request.method == 'POST':
        data = request.json
        new_target = MaterialTarget(
            topic=data['topic'], 
            target_date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            course_id=data['course_id']
        )
        db.session.add(new_target)
        db.session.commit()
        return jsonify({"message": "Target added"}), 201
    
    targets = MaterialTarget.query.all()
    return jsonify([{"id": t.id, "topic": t.topic, "completed": t.is_completed} for t in targets])

# ==========================================
# 5. ATTENDANCE TRACKING
# ==========================================
@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    course_id = request.args.get('course_id')
    date_str = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    
    if not course_id:
        return jsonify({"error": "course_id is required"}), 400
        
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    records = Attendance.query.filter_by(course_id=course_id, date=date_obj).all()
    
    return jsonify({
        "records": {r.student_id: r.status for r in records},
        "date": date_str,
        "course_id": course_id
    }), 200

@app.route('/api/attendance', methods=['POST'])
def mark_attendance():
    data = request.json or {}
    course_id = data.get('course_id')
    date_str = data.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    records = data.get('records', [])

    if not course_id or not isinstance(records, list) or len(records) == 0:
        return jsonify({"error": "course_id and records are required"}), 400

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        for record in records:
            student_id = record.get('student_id')
            status = record.get('status')
            if not student_id or not status:
                continue
            existing = Attendance.query.filter_by(
                student_id=student_id,
                course_id=course_id,
                date=date_obj
            ).first()
            if existing:
                existing.status = status
            else:
                db.session.add(Attendance(
                    student_id=student_id,
                    course_id=course_id,
                    status=status,
                    date=date_obj
                ))
        db.session.commit()
        return jsonify({"message": "Attendance recorded successfully"}), 200
    except Exception as exc:
        db.session.rollback()
        app.logger.exception("Attendance save failed: %s", exc)
        return jsonify({"error": "Failed to save attendance", "details": str(exc)}), 500

@app.route('/api/attendance/report/<int:course_id>', methods=['GET'])
def get_attendance_report(course_id):
    students = Student.query.filter_by(course_id=course_id).all()
    report = []
    
    for s in students:
        total_classes = Attendance.query.filter_by(student_id=s.id, course_id=course_id).count()
        present_count = Attendance.query.filter_by(student_id=s.id, course_id=course_id, status='Present').count()
        
        percentage = (present_count / total_classes * 100) if total_classes > 0 else 0
        
        report.append({
            "student_id": s.id,
            "name": s.name,
            "roll_number": s.roll_number,
            "total": total_classes,
            "present": present_count,
            "percentage": round(percentage, 2)
        })
        
    return jsonify(report), 200

@app.route('/api/courses/<int:course_id>/sync-students', methods=['POST'])
def sync_students_for_course(course_id):
    if 'credentials' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    course = Course.query.get(course_id)
    if not course:
        course = Course.query.filter_by(google_course_id=str(course_id)).first()
    if not course:
        return jsonify({"error": "Course not found. Sync courses first."}), 404
    if not course.google_course_id:
        return jsonify({"error": "Course not linked to Google Classroom"}), 400

    service = get_classroom_service()
    if not service:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        students_data = []
        page_token = None
        while True:
            resp = service.courses().students().list(
                courseId=course.google_course_id,
                pageToken=page_token,
                pageSize=100
            ).execute()
            students_data.extend(resp.get('students', []))
            page_token = resp.get('nextPageToken')
            if not page_token:
                break

        for s_data in students_data:
            profile = s_data.get('profile', {})
            student_id_google = profile.get('id')
            name = profile.get('name', {}).get('fullName', 'Unknown')
            existing = Student.query.filter_by(roll_number=student_id_google, course_id=course.id).first()
            if not existing:
                new_student = Student(
                    roll_number=student_id_google,
                    name=name,
                    course_id=course.id
                )
                db.session.add(new_student)
        
        db.session.commit()
        return jsonify({"message": f"Synced {len(students_data)} students successfully", "count": len(students_data)})
    except Exception as exc:
        app.logger.exception("Student sync failed: %s", exc)
        return jsonify({"error": str(exc)}), 500

@app.route('/api/courses/<int:course_id>/students', methods=['GET'])
def get_students(course_id):
    students = Student.query.filter_by(course_id=course_id).all()
    return jsonify([{
        "id": s.id,
        "name": s.name,
        "roll_number": s.roll_number
    } for s in students]), 200

# ==========================================
# 6. TIMETABLE AUTOMATION (Trigger)
# ==========================================
@app.route('/api/timetable/generate', methods=['POST'])
def generate_timetable():
    # Here you integrate the Genetic Algorithm from TechWithTim's logic
    # You would pass your DB Constraints to the algorithm and return the grid.
    return jsonify({"message": "Timetable generation algorithm triggered.", "status": "processing"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)



























