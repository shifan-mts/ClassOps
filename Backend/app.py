import os
# 1. Force HTTP for local testing (No HTTPS needed) - Must be set BEFORE imports
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from flask import Flask, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from flask_session import Session
from models import db, Teacher, Course, Student, Attendance, MaterialTarget, StudentMetric, Assignment
from dotenv import load_dotenv
import google.oauth2.credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import difflib
from openai import OpenAI
from datetime import datetime, timezone
from ai_checker import handle_upload, analyze_text, extract_text_from_file

load_dotenv()

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
    SESSION_PERMANENT=True,
    SESSION_USE_SIGNER=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True
)
Session(app)
db.init_app(app)

# ==========================================
# API KEYS (To be filled in .env file)
# ==========================================
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CLIENT_SECRETS_FILE = "client_secret.json" # Download from Google Cloud Console
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly', 
    'https://www.googleapis.com/auth/classroom.rosters.readonly',
    'https://www.googleapis.com/auth/classroom.student-submissions.students.readonly',
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]
GOOGLE_REDIRECT_URI = "http://localhost:5000/api/auth/google/callback"

# Initialize DB
with app.app_context():
    db.create_all()
    # Simple migration for SQLite (Add columns if they don't exist)
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            # Check Teacher table
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(teacher)")).fetchall()]
            if 'availability' not in cols:
                conn.execute(text("ALTER TABLE teacher ADD COLUMN availability JSON"))
            
            # Check Course table
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(course)")).fetchall()]
            if 'hours_per_week' not in cols:
                conn.execute(text("ALTER TABLE course ADD COLUMN hours_per_week INTEGER DEFAULT 3"))
            conn.commit()
    except Exception as e:
        app.logger.warning(f"Migration check skipped/failed: {e}")

@app.route('/api/debug/reset-db', methods=['POST'])
def reset_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
    return jsonify({"message": "Database reset successfully. All tables recreated."})


def get_classroom_service(credentials_dict=None):
    if credentials_dict is None:
        credentials_dict = session.get('credentials')
    if not credentials_dict:
        return None
    
    # Log current scopes for debugging
    app.logger.info(f"Current Token Scopes: {credentials_dict.get('scopes')}")
    
    creds = google.oauth2.credentials.Credentials(**credentials_dict)
    return build('classroom', 'v1', credentials=creds)


def sync_classroom_data(credentials_dict=None):
    service = get_classroom_service(credentials_dict)
    if not service:
        raise ValueError("Missing Google credentials. Please authenticate first.")

    # 1. Ensure Teacher exists
    user_info = session.get('user')
    if not user_info:
        raise ValueError("User info not found in session.")
    
    email = user_info.get('email')
    name = user_info.get('name', 'Unknown Teacher')
    
    teacher = Teacher.query.filter_by(email=email).first()
    if not teacher:
        teacher = Teacher(email=email, name=name)
        db.session.add(teacher)
        db.session.commit()

    # 2. Sync Courses
    results = service.courses().list(pageSize=10).execute()
    courses_data = results.get('courses', [])

    for c in courses_data:
        existing = Course.query.filter_by(google_course_id=c['id']).first()
        if not existing:
            new_course = Course(google_course_id=c['id'], name=c['name'], teacher_id=teacher.id)
            db.session.add(new_course)
        else:
            # Ensure teacher_id is correct
            existing.teacher_id = teacher.id
            
    db.session.commit()
    return courses_data

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
        include_granted_scopes='false', # Set to false to remove old permissions
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
        include_granted_scopes='false', # Set to false to remove old permissions
        prompt='consent',
        code_challenge_method='S256'
    )
    session['state'] = state
    session['code_verifier'] = flow.code_verifier
    session.modified = True
    return jsonify({"auth_url": authorization_url})

@app.route('/api/auth/google/callback')
def google_auth_callback():
    state = session.get('state')
    code_verifier = session.get('code_verifier')
    
    if not state:
        app.logger.error("No state found in session")
        return jsonify({"error": "Missing OAuth state. Please enable cookies and try again."}), 400
    if not code_verifier:
        app.logger.error("No code_verifier found in session")
        return jsonify({"error": "Missing OAuth code verifier. Please try again."}), 400

    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES, state=state
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI
        
        # Ensure we use the exact redirect URI origin to avoid mismatch
        authorization_response = request.url
        if GOOGLE_REDIRECT_URI.startswith('http://localhost') and '127.0.0.1' in authorization_response:
            authorization_response = authorization_response.replace('127.0.0.1', 'localhost')
        
        flow.fetch_token(authorization_response=authorization_response, code_verifier=code_verifier)

        credentials = flow.credentials
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        # Fetch User Profile
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        session['user'] = {
            'id': user_info.get('id'),
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture')
        }

        # Ensure teacher exists immediately upon login
        email = user_info.get('email')
        name = user_info.get('name', 'Unknown Teacher')
        teacher = Teacher.query.filter_by(email=email).first()
        if not teacher:
            teacher = Teacher(email=email, name=name)
            db.session.add(teacher)
            db.session.commit()

        try:
            sync_classroom_data(session['credentials'])
        except Exception as exc:
            app.logger.exception("Classroom sync failed: %s", exc)
        
        return redirect('http://localhost:5173/') # Redirect to React App
    except Exception as e:
        app.logger.exception("OAuth callback error: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/me')
def get_me():
    if 'user' not in session:
        return jsonify({"authenticated": False}), 401
    
    # Check current scopes
    creds = session.get('credentials', {})
    app.logger.info(f"Checking session for {session['user'].get('email')} | Current Token Scopes: {creds.get('scopes')}")
    
    return jsonify({"authenticated": True, "user": session['user']})

@app.route('/api/auth/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    # Path to session files to avoid oversized payloads
    session_id = request.cookies.get('session')
    response = jsonify({"message": "Logged out successfully"})
    response.delete_cookie('session')
    return response, 200

@app.route('/api/classroom/sync')
def sync_classroom():
    if 'credentials' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    courses = sync_classroom_data(session['credentials'])
    return jsonify({"message": "Classroom synced successfully", "courses": courses})

@app.route('/api/courses', methods=['GET'])
def get_courses():
    courses = Course.query.all()
    return jsonify([{"id": c.id, "google_course_id": c.google_course_id, "name": c.name} for c in courses])

@app.route('/api/courses/<int:course_id>/sync-assignments', methods=['POST'])
def sync_assignments(course_id):
    service = get_classroom_service()
    if not service:
        return jsonify({"error": "Not authenticated"}), 401
    
    course = Course.query.get_or_404(course_id)
    if not course.google_course_id:
        return jsonify({"error": "Course not linked to Google Classroom"}), 400

    try:
        results = service.courses().courseWork().list(courseId=course.google_course_id).execute()
        coursework_data = results.get('courseWork', [])

        count = 0
        for cw in coursework_data:
            existing = Assignment.query.filter_by(google_assignment_id=cw['id']).first()
            if not existing:
                new_assignment = Assignment(
                    google_assignment_id=cw['id'],
                    title=cw['title'],
                    course_id=course.id
                )
                db.session.add(new_assignment)
                count += 1
        
        db.session.commit()
        return jsonify({"message": f"Synced {count} new assignments successfully"}), 200
    except Exception as exc:
        app.logger.exception("Assignment sync failed: %s", exc)
        return jsonify({"error": f"Classroom API error: {str(exc)}"}), 500

@app.route('/api/courses/<int:course_id>/assignments', methods=['GET'])
def get_assignments(course_id):
    assignments = Assignment.query.filter_by(course_id=course_id).all()
    return jsonify([{"id": a.id, "google_assignment_id": a.google_assignment_id, "title": a.title} for a in assignments])

@app.route('/api/assignments/check', methods=['POST'])
def check_plagiarism():
    if 'file' in request.files:
        file = request.files['file']
        if not file or not file.filename:
            return jsonify({"error": "No file uploaded"}), 400
        result = handle_upload(file)
        status_code = 200 if result.get("success") else 500
        return jsonify(result), status_code

    data = request.get_json(silent=True) or {}
    text_to_check = data.get('text')
    if text_to_check:
        result = analyze_text(text_to_check)
        status_code = 200 if result.get("success") else 500
        return jsonify(result), status_code

    return jsonify({"error": "Provide a file upload or a text field."}), 400

@app.route('/api/assignments/<int:assignment_id>/analyze', methods=['POST'])
def analyze_submissions(assignment_id):
    from ai_checker import run_batch_analysis
    service = get_classroom_service()
    if not service:
        return jsonify({"error": "Not authenticated with Google Classroom"}), 401
    
    assignment = Assignment.query.get_or_404(assignment_id)
    course = assignment.course

    try:
        # 1. Fetch submissions
        results = service.courses().courseWork().studentSubmissions().list(
            courseId=course.google_course_id,
            courseWorkId=assignment.google_assignment_id
        ).execute()
        submissions = results.get('studentSubmissions', [])

        if not submissions:
            return jsonify({"message": "No submissions found to analyze.", "results": [], "alerts": []}), 200

        # 2. Map student names from local DB
        local_students = Student.query.filter_by(course_id=course.id).all()
        student_map = {s.roll_number: s.name for s in local_students}

        # 3. Prepare data for analysis
        batch_input = []
        for sub in submissions[:15]: 
            uid = sub.get('userId')
            name = student_map.get(uid, f"Student {uid}")
            
            content = ""
            file_info = ""
            
            if 'shortAnswerSubmission' in sub:
                content = sub['shortAnswerSubmission'].get('answer', "")
            
            elif 'assignmentSubmission' in sub and 'attachments' in sub['assignmentSubmission']:
                # Google Drive API is disabled as per user request. 
                # We can't download files without it.
                attachments = sub['assignmentSubmission']['attachments']
                file_names = []
                for att in attachments:
                    if 'driveFile' in att:
                        file_names.append(att['driveFile'].get('title', "Untitled"))
                
                if file_names:
                    file_info = f" [Files: {', '.join(file_names)}]"
                    content = f"Note: This student submitted files ({', '.join(file_names)}). Automated analysis for Google Drive files is currently disabled (requires Drive API)."

            if not content or content.strip() == "":
                content = f"Empty submission or unsupported format from {name}."
            
            batch_input.append({
                "name": name + file_info, 
                "content": content
            })

        # 4. Run Analysis (LOCAL AI + SEPARATE PLAGIARISM)
        analysis_data = run_batch_analysis(batch_input)

        # 5. Format for Frontend (App.jsx expects .results and .alerts)
        # Transform ai_results -> results
        # Transform plagiarism_results -> alerts
        
        formatted_results = []
        for r in analysis_data['ai_results']:
            formatted_results.append({
                "name": r['name'],
                "ai_score": r['ai_score'],
                "status": r['status']
            })
            
        formatted_alerts = []
        for p in analysis_data['plagiarism_results']:
            if "❌" in p['status']:
                formatted_alerts.append({
                    "students": [p['name'], p['matched_with']],
                    "score": p['highest_match_percent']
                })

        return jsonify({
            "success": True,
            "results": formatted_results,
            "alerts": formatted_alerts,
            "submission_count": len(submissions)
        })

    except Exception as exc:
        app.logger.exception("Analysis failed: %s", exc)
        return jsonify({"error": f"Analysis failed: {str(exc)}"}), 500

# ==========================================
# 3. QUESTION PAPER CREATION (BLOOM'S TAXONOMY & CO MAPPING)
# ==========================================
@app.route('/api/question-paper/generate', methods=['POST'])
def generate_question_paper():
    data = request.json
    topic = data.get('topic')
    difficulty = data.get('difficulty', 'Medium')
    course_name = data.get('course_name', 'General Course')

    if not OPENAI_API_KEY:
        return jsonify({"error": "OpenAI API key is missing. Set OPENAI_API_KEY in .env."}), 400

    prompt = f"""Generate a university-level question paper for the course '{course_name}' on the topic '{topic}' with a '{difficulty}' difficulty. 
    The question paper MUST strictly follow Bloom's Taxonomy and include Course Outcome (CO) mapping for each question.
    
    Structure:
    Part A (Remember & Understand - L1/L2): 5 short questions (2 marks each). Map to CO1/CO2.
    Part B (Apply & Analyze - L3/L4): 3 medium questions (5 marks each). Map to CO3/CO4.
    Part C (Evaluate & Create - L5/L6): 2 essay questions (10 marks each). Map to CO5/CO6.

    For each question, indicate the Bloom's Level (e.g., L1) and the mapped CO (e.g., CO1).
    Format the output clearly with headings and a table-like structure if possible.
    """

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert university professor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        content = ""
        if response.choices:
            content = response.choices[0].message.content
        return jsonify({"question_paper": content})
    except Exception as exc:
        app.logger.exception("Failed to generate question paper: %s", exc)
        error_msg = str(exc)
        if "insufficient_quota" in error_msg:
            return jsonify({
                "error": "OpenAI API quota exhausted. Please check your billing details or plan at platform.openai.com.",
                "details": error_msg
            }), 429
        return jsonify({"error": "Failed to generate question paper.", "details": error_msg}), 500


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
    date_str = request.args.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
    
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
    data = request.json
    course_id = data.get('course_id')
    date_str = data.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

    if not course_id or 'records' not in data:
        return jsonify({"error": "course_id and records are required"}), 400

    for record in data['records']: # List of {student_id, status}
        # Check if record already exists for this student on this date
        existing = Attendance.query.filter_by(
            student_id=record['student_id'], 
            course_id=course_id, 
            date=date_obj
        ).first()
        
        if existing:
            existing.status = record['status']
        else:
            att = Attendance(
                student_id=record['student_id'], 
                course_id=course_id, 
                status=record['status'], 
                date=date_obj
            )
            db.session.add(att)
            
    db.session.commit()
    return jsonify({"message": "Attendance recorded successfully"}), 200

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
    service = get_classroom_service()
    if not service:
        return jsonify({"error": "Not authenticated"}), 401
    
    course = Course.query.get_or_404(course_id)
    if not course.google_course_id:
        return jsonify({"error": "Course not linked to Google Classroom"}), 400

    try:
        results = service.courses().students().list(courseId=course.google_course_id).execute()
        students_data = results.get('students', [])

        count = 0
        for s_data in students_data:
            # userId is always present in a Student resource
            student_id_google = s_data.get('userId')
            if not student_id_google:
                continue

            profile = s_data.get('profile', {})
            name = profile.get('name', {}).get('fullName', 'Unknown Student')
            
            # Check if student exists in this course
            existing = Student.query.filter_by(roll_number=student_id_google, course_id=course.id).first()
            if not existing:
                new_student = Student(
                    roll_number=student_id_google, 
                    name=name, 
                    course_id=course.id
                )
                db.session.add(new_student)
                count += 1
        
        db.session.commit()
        return jsonify({"message": f"Synced {count} new students successfully"}), 200
    except Exception as exc:
        app.logger.exception("Student sync failed: %s", exc)
        return jsonify({"error": f"Classroom API error: {str(exc)}"}), 500

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
@app.route('/api/teacher/profile', methods=['GET', 'POST'])
def teacher_profile():
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    email = session['user'].get('email')
    teacher = Teacher.query.filter_by(email=email).first()
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404

    if request.method == 'POST':
        data = request.json
        if 'availability' in data:
            teacher.availability = data['availability']
        if 'name' in data:
            teacher.name = data['name']
        
        # Also update hours_per_week for courses if provided
        if 'courses' in data:
            for c_data in data['courses']:
                course = Course.query.get(c_data['id'])
                if course and course.teacher_id == teacher.id:
                    course.hours_per_week = c_data.get('hours', course.hours_per_week)
        
        db.session.commit()
        return jsonify({"message": "Profile updated successfully"})

    # GET request
    return jsonify({
        "name": teacher.name,
        "availability": teacher.availability or {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]},
        "courses": [{"id": c.id, "name": c.name, "hours": c.hours_per_week} for c in teacher.courses]
    })

@app.route('/api/timetable/generate', methods=['POST'])
def generate_timetable():
    from scheduler import run_backtracking_scheduler
    
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    email = session['user'].get('email')
    teacher = Teacher.query.filter_by(email=email).first()
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404

    # Prepare inputs for scheduler
    availability = teacher.availability or {}
    courses_to_schedule = []
    for c in teacher.courses:
        courses_to_schedule.append({
            'id': c.id,
            'name': c.name,
            'hours': c.hours_per_week
        })

    # Run scheduler
    new_slots = run_backtracking_scheduler(availability, courses_to_schedule)
    
    if new_slots is None:
        return jsonify({"error": "Could not generate a feasible timetable. Try increasing availability."}), 400

    # Persist timetable
    # 1. Clear old timetable
    if teacher.timetable:
        db.session.delete(teacher.timetable)
    
    # 2. Create new one
    timetable = Timetable(teacher_id=teacher.id)
    db.session.add(timetable)
    db.session.commit() # Get timetable ID

    for slot in new_slots:
        ts = TimetableSlot(
            timetable_id=timetable.id,
            day=slot['day'],
            period=slot['period'],
            course_id=slot['course_id'],
            subject=slot['subject']
        )
        db.session.add(ts)
    
    db.session.commit()

    return jsonify({"message": "Timetable generated and saved.", "timetable_id": timetable.id})

@app.route('/api/timetable', methods=['GET'])
def get_timetable():
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    email = session['user'].get('email')
    teacher = Teacher.query.filter_by(email=email).first()
    if not teacher or not teacher.timetable:
        return jsonify({"message": "No timetable found.", "timetable": {}}), 200

    # Format into a nested dict for frontend
    result = {}
    # Initialize with course IDs
    for c in teacher.courses:
        result[c.id] = {day: {} for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
    
    for slot in teacher.timetable.slots:
        if slot.course_id not in result:
            result[slot.course_id] = {day: {} for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
        
        result[slot.course_id][slot.day][slot.period] = {
            "sub": slot.subject,
            "className": slot.course.name
        }

    return jsonify({"timetable": result})

if __name__ == '__main__':
    app.run(debug=True, port=5000)












