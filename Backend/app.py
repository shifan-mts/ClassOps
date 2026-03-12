import os
# 1. Force HTTP for local testing (No HTTPS needed) - Must be set BEFORE imports
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from flask import Flask, request, jsonify, redirect, url_for, session, send_file
from flask_cors import CORS
from flask_session import Session
from models import db, Teacher, Course, Student, Attendance, MaterialTarget, StudentMetric, Assignment, Timetable, TimetableSlot
from dotenv import load_dotenv
import google.oauth2.credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import io
import difflib
import json
from google import genai
from google.genai import types
from datetime import datetime, timezone
from io import BytesIO
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from textwrap import wrap
from ai_checker import handle_upload, analyze_text, extract_text_from_file

load_dotenv()

def normalize_api_key(value):
    if not value:
        return None
    cleaned = str(value).strip()
    if (cleaned.startswith('\"') and cleaned.endswith('\"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()
    cleaned = cleaned.strip()
    return cleaned if cleaned else None



def get_qp_header(data, course_name):
    return {
        "college_name": data.get('college_name') or os.getenv('QP_COLLEGE_NAME', 'COLLEGE NAME'),
        "college_address": data.get('college_address') or os.getenv('QP_COLLEGE_ADDRESS', ''),
        "affiliation": data.get('affiliation') or os.getenv('QP_AFFILIATION', ''),
        "academic_year": data.get('academic_year') or os.getenv('QP_ACADEMIC_YEAR', ''),
        "assessment": data.get('assessment') or os.getenv('QP_ASSESSMENT', 'Assessment Test - II'),
        "course_code": data.get('course_code') or os.getenv('QP_COURSE_CODE', ''),
        "course_title": data.get('course_title') or course_name,
        "date": data.get('date') or os.getenv('QP_DATE', datetime.now().strftime('%d/%m/%Y')),
        "time": data.get('time') or os.getenv('QP_TIME', ''),
        "max_marks": data.get('max_marks') or os.getenv('QP_MAX_MARKS', '')
    }


def build_qp_prompt(topic, course_name, difficulty, part_a_count, part_b_count, part_c_count):
    return f"""Generate a university assessment question paper.
Return ONLY a JSON object matching the response schema. No extra text.

Rules:
- Part A: {part_a_count} short questions (2 marks each).
- Part B: {part_b_count} long questions (16 marks each) with OR alternatives.
- Part C: {part_c_count} long questions (8 marks each) with OR alternatives.
- Keep each question under 20 words.
- Use CO1-CO5 and K1-K6.

Topic: {topic}. Course: {course_name}. Difficulty: {difficulty}.
"""


def get_qp_schema(part_a_count, part_b_count, part_c_count):
    part_a_item = {
        "type": "object",
        "required": ["question", "co", "bloom"],
        "properties": {
            "question": {"type": "string"},
            "co": {"type": "string"},
            "bloom": {"type": "string"}
        }
    }
    part_b_item = {
        "type": "object",
        "required": ["question", "co", "bloom", "or_question", "or_co", "or_bloom"],
        "properties": {
            "question": {"type": "string"},
            "co": {"type": "string"},
            "bloom": {"type": "string"},
            "or_question": {"type": "string"},
            "or_co": {"type": "string"},
            "or_bloom": {"type": "string"}
        }
    }
    part_c_item = {
        "type": "object",
        "required": ["question", "co", "bloom", "or_question", "or_co", "or_bloom"],
        "properties": {
            "question": {"type": "string"},
            "co": {"type": "string"},
            "bloom": {"type": "string"},
            "or_question": {"type": "string"},
            "or_co": {"type": "string"},
            "or_bloom": {"type": "string"}
        }
    }
    return {
        "type": "object",
        "required": ["part_a", "part_b", "part_c"],
        "properties": {
            "part_a": {"type": "array", "items": part_a_item, "minItems": part_a_count, "maxItems": part_a_count},
            "part_b": {"type": "array", "items": part_b_item, "minItems": part_b_count, "maxItems": part_b_count},
            "part_c": {"type": "array", "items": part_c_item, "minItems": part_c_count, "maxItems": part_c_count}
        }
    }


def parse_qp_json(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def normalize_qp(qp, part_a_count, part_b_count, part_c_count):
    if not isinstance(qp, dict):
        return None
    part_a = qp.get('part_a') or []
    part_b = qp.get('part_b') or []
    part_c = qp.get('part_c') or []

    if len(part_a) < part_a_count or len(part_b) < part_b_count or len(part_c) < part_c_count:
        return None

    qp['part_a'] = part_a[:part_a_count]
    qp['part_b'] = part_b[:part_b_count]
    qp['part_c'] = part_c[:part_c_count]
    return qp


def render_qp_text(qp, part_a_count, part_b_count, part_c_count):
    lines = []
    part_a = qp.get('part_a', [])
    part_b = qp.get('part_b', [])
    part_c = qp.get('part_c', [])

    lines.append(f"PART - A ({part_a_count} x 2 = {part_a_count * 2} marks)")
    lines.append("Answer all the Questions")
    for idx, q in enumerate(part_a, start=1):
        lines.append(f"{idx}. {q.get('question', '')} (CO: {q.get('co', '')}, {q.get('bloom', '')})")

    lines.append(f"\nPART - B (2 x 16 = 32 marks)")
    for i, q in enumerate(part_b, start=1):
        no = part_a_count + i
        lines.append(f"{no}(a). {q.get('question', '')} (CO: {q.get('co', '')}, {q.get('bloom', '')})")
        lines.append("OR")
        lines.append(f"{no}(b). {q.get('or_question', '')} (CO: {q.get('or_co', '')}, {q.get('or_bloom', '')})")

    lines.append(f"\nPART - C (1 x 8 = 8 marks)")
    for i, q in enumerate(part_c, start=1):
        no = part_a_count + part_b_count + i
        lines.append(f"{no}(a). {q.get('question', '')} (CO: {q.get('co', '')}, {q.get('bloom', '')})")
        lines.append("OR")
        lines.append(f"{no}(b). {q.get('or_question', '')} (CO: {q.get('or_co', '')}, {q.get('or_bloom', '')})")

    return "".join(lines)


def build_question_paper_docx(header, qp, part_a_count, part_b_count, part_c_count):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(11)

    reg = doc.add_paragraph()
    reg.add_run("Reg.No.: ").bold = True
    reg.add_run("____________________")

    def add_center_line(text, bold=False):
        if not text:
            return
        p = doc.add_paragraph()
        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run = p.add_run(text)
        run.bold = bold

    college_line = header.get('college_name')
    if header.get('college_address'):
        college_line = f"{college_line}, {header.get('college_address')}".strip(', ')
    add_center_line(college_line, bold=True)
    add_center_line(header.get('affiliation'))
    add_center_line(header.get('academic_year'))
    add_center_line(header.get('assessment'), bold=True)

    course_code = header.get('course_code')
    course_title = header.get('course_title')
    if course_code and course_title:
        add_center_line(f"{course_code} - {course_title}", bold=True)
    else:
        add_center_line(course_title, bold=True)

    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    left = table.rows[0].cells[0]
    right = table.rows[0].cells[1]
    left.text = f"Time: {header.get('time') or '__________'}"
    right.text = f"Date: {header.get('date') or '__________'}"

    max_marks = header.get('max_marks')
    if max_marks:
        p = doc.add_paragraph()
        p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        p.add_run(f"Max. Marks: {max_marks}")

    def add_part(title, instruction, questions, start_no, with_or):
        p = doc.add_paragraph()
        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        p.add_run(title).bold = True
        if instruction:
            p2 = doc.add_paragraph()
            p2.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            p2.add_run(instruction)

        t = doc.add_table(rows=1, cols=4)
        t.style = 'Table Grid'
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr = t.rows[0].cells
        hdr[0].text = "S.No."
        hdr[1].text = "Questions"
        hdr[2].text = "Course Outcome"
        hdr[3].text = "Bloom's Taxonomy level"

        for i, q in enumerate(questions, start=0):
            no = start_no + i
            if with_or:
                row_a = t.add_row().cells
                row_a[0].text = f"{no}(a)"
                row_a[1].text = q.get('question', '')
                row_a[2].text = q.get('co', '')
                row_a[3].text = q.get('bloom', '')

                or_row = t.add_row().cells
                or_row[1].text = "OR"
                or_row[1].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

                row_b = t.add_row().cells
                row_b[0].text = f"{no}(b)"
                row_b[1].text = q.get('or_question', '')
                row_b[2].text = q.get('or_co', '')
                row_b[3].text = q.get('or_bloom', '')
            else:
                row = t.add_row().cells
                row[0].text = str(no)
                row[1].text = q.get('question', '')
                row[2].text = q.get('co', '')
                row[3].text = q.get('bloom', '')

    part_a = qp.get('part_a', [])
    part_b = qp.get('part_b', [])
    part_c = qp.get('part_c', [])

    add_part(f"PART - A ({part_a_count} x 2 = {part_a_count * 2} marks)", "Answer all the Questions", part_a, 1, False)
    add_part("PART - B (2 x 16 = 32 marks)", None, part_b, part_a_count + 1, True)
    add_part("PART - C (1 x 8 = 8 marks)", None, part_c, part_a_count + part_b_count + 1, True)

    out = BytesIO()
    doc.save(out)
    out.seek(0)
    return out


def get_drive_service(credentials_dict=None):
    if credentials_dict is None:
        credentials_dict = session.get('credentials')
    if not credentials_dict:
        return None
    creds = google.oauth2.credentials.Credentials(**credentials_dict)
    return build('drive', 'v3', credentials=creds)

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
GEMINI_API_KEY = normalize_api_key(os.getenv('GEMINI_API_KEY'))
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')
CLIENT_SECRETS_FILE = "client_secret.json" # Download from Google Cloud Console
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly', 
    'https://www.googleapis.com/auth/classroom.rosters.readonly',
    'https://www.googleapis.com/auth/classroom.student-submissions.students.readonly',
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/drive.file'
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
    
    sync_classroom_data(session['credentials'])
    email = session.get('user', {}).get('email')
    teacher = Teacher.query.filter_by(email=email).first() if email else None
    courses = Course.query.filter_by(teacher_id=teacher.id).all() if teacher else []
    return jsonify({
        "message": "Classroom synced successfully",
        "courses": [{"id": c.id, "google_course_id": c.google_course_id, "name": c.name} for c in courses]
    })

@app.route('/api/courses', methods=['GET'])
def get_courses():
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    email = session.get('user', {}).get('email')
    teacher = Teacher.query.filter_by(email=email).first() if email else None
    courses = Course.query.filter_by(teacher_id=teacher.id).all() if teacher else []
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
                content = "" # Explicitly empty so ai_checker identifies it as "No File"
                file_info = " [No Submission]"
            
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
        formatted_plagiarism = []
        for p in analysis_data['plagiarism_results']:
            # For the general list
            formatted_plagiarism.append({
                "name": p['name'],
                "status": p['status'],
                "matched_with": p.get('matched_with', 'N/A'),
                "score": p.get('highest_match_percent', 0)
            })
            
            # For specific red alerts
            if "?" in p['status']:
                formatted_alerts.append({
                    "students": [p['name'], p['matched_with']],
                    "score": p['highest_match_percent']
                })

        return jsonify({
            "success": True,
            "results": formatted_results,
            "plagiarism": formatted_plagiarism,
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
    data = request.get_json(silent=True) or {}
    topic = (data.get('topic') or '').strip()
    if not topic:
        return jsonify({"error": "topic is required"}), 400

    difficulty = data.get('difficulty', 'Medium')
    course_name = data.get('course_name', 'General Course')
    output = data.get('output', 'text')

    part_a_count = 5
    part_b_count = 2
    part_c_count = 1


    header = get_qp_header(data, course_name)

    # Use key from request if provided, otherwise fallback to server env
    custom_key = normalize_api_key(data.get('api_key'))
    env_key = normalize_api_key(GEMINI_API_KEY) or normalize_api_key(os.getenv('GEMINI_API_KEY'))
    effective_key = custom_key if custom_key else env_key

    if not effective_key:
        return jsonify({"error": "Gemini API key is missing. Please provide one in the input box below."}), 400

    prompt = build_qp_prompt(topic, course_name, difficulty, part_a_count, part_b_count, part_c_count)

    try:
        client = genai.Client(api_key=effective_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=900, response_mime_type="application/json", response_schema=get_qp_schema(part_a_count, part_b_count, part_c_count))
        )
        raw_text = ""
        if response is not None:
            raw_text = getattr(response, "text", "") or ""

        qp = getattr(response, "parsed", None)
        if not qp:
            qp = parse_qp_json(raw_text)
        qp = normalize_qp(qp, part_a_count, part_b_count, part_c_count)
        if not qp:
            if output == 'text':
                return jsonify({"question_paper": raw_text})
            return jsonify({"error": "Failed to parse structured question paper. Try again."}), 500

        if output == 'text':
            rendered = render_qp_text(qp, part_a_count, part_b_count, part_c_count)
            return jsonify({"question_paper": rendered})

        docx_bytes = build_question_paper_docx(header, qp, part_a_count, part_b_count, part_c_count)
        safe_course = (course_name or 'question_paper').replace(' ', '_').replace('/', '_')
        filename = f"question_paper_{safe_course}_{datetime.now().strftime('%Y%m%d')}.docx"

        if output == 'google_doc':
            if 'credentials' not in session:
                return jsonify({"error": "Not authenticated with Google. Please sign in again to grant Drive access."}), 401
            drive = get_drive_service()
            if not drive:
                return jsonify({"error": "Google Drive service unavailable."}), 500
            docx_bytes.seek(0)
            media = MediaIoBaseUpload(docx_bytes, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document', resumable=False)
            file_metadata = {"name": filename.replace('.docx', ''), "mimeType": "application/vnd.google-apps.document"}
            created = drive.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
            return jsonify({"doc_url": created.get('webViewLink'), "doc_id": created.get('id')})

        return send_file(docx_bytes, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    except Exception as exc:
        app.logger.exception("Failed to generate question paper: %s", exc)
        error_msg = str(exc)
        status_code = getattr(exc, "status_code", None) or getattr(exc, "status", None)
        if status_code is None:
            if "Error code: 401" in error_msg or "UNAUTHENTICATED" in error_msg or "API key" in error_msg or "permission" in error_msg.lower():
                status_code = 401
            elif "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                status_code = 429
        if status_code == 401:
            return jsonify({
                "error": "Invalid Gemini API key. Please update your key and try again.",
                "details": error_msg
            }), 401
        if status_code == 429 or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
            return jsonify({
                "error": "Gemini API quota exhausted. Please check your Google AI Studio billing and quota settings.",
                "details": error_msg
            }), 429
        return jsonify({"error": "Failed to generate question paper.", "details": error_msg}), status_code or 500


# ==========================================
# 4. MATERIAL TARGET COMPLETION
# ==========================================

# ==========================================
@app.route('/api/targets', methods=['GET', 'POST'])
def manage_targets():
    if request.method == 'POST':
        data = request.json or {}
        if not data.get('topic') or not data.get('date') or not data.get('course_id'):
            return jsonify({"error": "topic, date, and course_id are required"}), 400
        new_target = MaterialTarget(
            topic=data['topic'], 
            target_date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            course_id=data['course_id']
        )
        db.session.add(new_target)
        db.session.commit()
        return jsonify({
            "id": new_target.id,
            "topic": new_target.topic,
            "completed": new_target.is_completed,
            "date": new_target.target_date.strftime('%Y-%m-%d'),
            "course_id": new_target.course_id,
            "course_name": new_target.course.name if new_target.course else None
        }), 201
    
    course_id = request.args.get('course_id')
    query = MaterialTarget.query
    if course_id:
        try:
            course_id = int(course_id)
        except ValueError:
            return jsonify({"error": "course_id must be an integer"}), 400
        query = query.filter_by(course_id=course_id)
    targets = query.order_by(MaterialTarget.target_date.asc()).all()
    return jsonify([
        {
            "id": t.id,
            "topic": t.topic,
            "completed": t.is_completed,
            "date": t.target_date.strftime('%Y-%m-%d'),
            "course_id": t.course_id,
            "course_name": t.course.name if t.course else None
        }
        for t in targets
    ])

@app.route('/api/targets/<int:target_id>', methods=['PATCH'])
def update_target(target_id):
    data = request.json or {}
    target = MaterialTarget.query.get_or_404(target_id)
    if 'topic' in data and data['topic']:
        target.topic = data['topic']
    if 'date' in data and data['date']:
        target.target_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    if 'completed' in data:
        target.is_completed = bool(data['completed'])
    db.session.commit()
    return jsonify({
        "id": target.id,
        "topic": target.topic,
        "completed": target.is_completed,
        "date": target.target_date.strftime('%Y-%m-%d'),
        "course_id": target.course_id,
        "course_name": target.course.name if target.course else None
    }), 200

# ==========================================

# ==========================================
# 4B. COMPLIANCE METRICS & REPORTS
# ==========================================

def compute_compliance_metrics(course_id=None):
    targets_query = MaterialTarget.query
    attendance_query = Attendance.query

    if course_id:
        targets_query = targets_query.filter_by(course_id=course_id)
        attendance_query = attendance_query.filter_by(course_id=course_id)

    total_targets = targets_query.count()
    completed_targets = targets_query.filter_by(is_completed=True).count()
    pending_targets = max(0, total_targets - completed_targets)
    co_coverage = round((completed_targets / total_targets) * 100) if total_targets else 0

    total_attendance = attendance_query.count()
    present_count = attendance_query.filter_by(status='Present').count()
    po_mapping = round((present_count / total_attendance) * 100) if total_attendance else 0

    if total_targets == 0:
        status = "No targets yet"
    else:
        status = "On track" if completed_targets >= pending_targets else "Needs attention"

    return {
        "co_coverage": co_coverage,
        "po_mapping": po_mapping,
        "status": status,
        "completed_targets": completed_targets,
        "pending_targets": pending_targets,
        "total_targets": total_targets,
        "attendance_records": total_attendance,
        "present_records": present_count
    }


def collect_report_data(course_id=None):
    if course_id:
        courses = Course.query.filter_by(id=course_id).all()
        students = Student.query.filter_by(course_id=course_id).all()
        targets = MaterialTarget.query.filter_by(course_id=course_id).all()
        assignments = Assignment.query.filter_by(course_id=course_id).all()
        slots = TimetableSlot.query.filter_by(course_id=course_id).all()
        attendance_records = Attendance.query.filter_by(course_id=course_id).all()
    else:
        courses = Course.query.all()
        students = Student.query.all()
        targets = MaterialTarget.query.all()
        assignments = Assignment.query.all()
        slots = TimetableSlot.query.all()
        attendance_records = Attendance.query.all()

    attendance_summary = []
    for student in students:
        total_classes = Attendance.query.filter_by(student_id=student.id, course_id=student.course_id).count()
        present_count = Attendance.query.filter_by(student_id=student.id, course_id=student.course_id, status='Present').count()
        percentage = round((present_count / total_classes) * 100, 1) if total_classes else 0
        attendance_summary.append({
            "name": student.name,
            "roll_number": student.roll_number,
            "course_id": student.course_id,
            "total_classes": total_classes,
            "present_count": present_count,
            "percentage": percentage
        })

    return {
        "courses": courses,
        "students": students,
        "targets": targets,
        "assignments": assignments,
        "timetable_slots": slots,
        "attendance_summary": attendance_summary,
        "attendance_records": attendance_records
    }


@app.route('/api/metrics/compliance', methods=['GET'])
def get_compliance_metrics():
    course_id = request.args.get('course_id')
    if course_id:
        try:
            course_id = int(course_id)
        except ValueError:
            return jsonify({"error": "course_id must be an integer"}), 400

    metrics = compute_compliance_metrics(course_id)
    return jsonify(metrics), 200


@app.route('/api/reports/compliance.pdf', methods=['GET'])
def generate_compliance_report():
    course_id = request.args.get('course_id')
    if course_id:
        try:
            course_id = int(course_id)
        except ValueError:
            return jsonify({"error": "course_id must be an integer"}), 400

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except Exception:
        return jsonify({"error": "PDF generation requires reportlab. Install it and restart the backend."}), 500
    metrics = compute_compliance_metrics(course_id)
    data = collect_report_data(course_id)
    student_map = {s.id: s for s in data['students']}
    course_map = {c.id: c for c in data['courses']}

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    x = 40
    y = height - 40

    def write_line(line):
        nonlocal y
        for chunk in wrap(str(line), width=95) or [""]:
            if y < 40:
                pdf.showPage()
                y = height - 40
            pdf.drawString(x, y, chunk)
            y -= 14

    write_line("ClassOps NBA/NAAC Compliance Report")
    write_line(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if course_id and data['courses']:
        write_line(f"Course: {data['courses'][0].name}")
    write_line("")

    write_line("Compliance Metrics")
    write_line(f"CO Coverage: {metrics['co_coverage']}%")
    write_line(f"PO Mapping: {metrics['po_mapping']}%")
    write_line(f"Status: {metrics['status']}")
    write_line("")

    write_line("Courses")
    if data['courses']:
        for course in data['courses']:
            write_line(f"- {course.name} (ID: {course.id})")
    else:
        write_line("No courses found.")
    write_line("")

    write_line("Students")
    if data['students']:
        for student in data['students']:
            course = course_map.get(student.course_id)
            course_name = course.name if course else f"Course {student.course_id}"
            write_line(f"- {student.name} ({student.roll_number}) | {course_name}")
    else:
        write_line("No students found.")
    write_line("")

    write_line("Syllabus Targets")
    if data['targets']:
        for target in data['targets']:
            status = "Completed" if target.is_completed else "Pending"
            course_name = target.course.name if target.course else ""
            write_line(f"- {target.topic} | Due: {target.target_date} | {status} | {course_name}")
    else:
        write_line("No targets found.")
    write_line("")

    write_line("Attendance Summary")
    if data['attendance_summary']:
        for entry in data['attendance_summary']:
            write_line(f"- {entry['name']} ({entry['roll_number']}): {entry['percentage']}% ({entry['present_count']}/{entry['total_classes']})")
    else:
        write_line("No attendance data found.")
    write_line("")

    write_line("Attendance Records")
    if data['attendance_records']:
        for record in data['attendance_records']:
            student = student_map.get(record.student_id)
            course = course_map.get(record.course_id)
            student_label = f"{student.name} ({student.roll_number})" if student else f"Student {record.student_id}"
            course_label = course.name if course else f"Course {record.course_id}"
            write_line(f"- {record.date} | {student_label} | {course_label} | {record.status}")
    else:
        write_line("No attendance records found.")
    write_line("")

    write_line("Assignments")
    if data['assignments']:
        for assignment in data['assignments']:
            write_line(f"- {assignment.title} (Course ID: {assignment.course_id})")
    else:
        write_line("No assignments found.")
    write_line("")

    write_line("Timetable")
    if data['timetable_slots']:
        for slot in data['timetable_slots']:
            course_name = slot.course.name if slot.course else ""
            write_line(f"- {slot.day} P{slot.period + 1}: {slot.subject} ({course_name})")
    else:
        write_line("No timetable slots found.")

    pdf.save()
    buffer.seek(0)

    filename = "nba_compliance_report.pdf"
    if course_id and data['courses']:
        safe_name = "_".join(data['courses'][0].name.lower().split())
        filename = f"nba_compliance_report_{safe_name}.pdf"

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )
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

@app.route('/api/courses/<course_id>/sync-students', methods=['POST'])
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

@app.route('/api/config/update-key', methods=['POST'])
def update_api_key():
    data = request.json
    new_key = normalize_api_key(data.get('api_key'))
    if not new_key:
        return jsonify({"error": "No API key provided"}), 400

    env_path = os.path.join(os.path.dirname(__file__), '.env')
    try:
        # Read existing .env content
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()

        # Update or add GEMINI_API_KEY
        key_found = False
        new_lines = []
        for line in lines:
            if line.startswith('GEMINI_API_KEY='):
                new_lines.append(f'GEMINI_API_KEY={new_key}\n')
                key_found = True
            else:
                new_lines.append(line)
        
        if not key_found:
            new_lines.append(f'GEMINI_API_KEY={new_key}\n')

        # Write back to .env
        with open(env_path, 'w') as f:
            f.writelines(new_lines)

        # Update current process variable
        global GEMINI_API_KEY
        GEMINI_API_KEY = new_key
        os.environ['GEMINI_API_KEY'] = new_key

        return jsonify({"message": "API Key updated successfully in .env and server memory."})
    except Exception as e:
        app.logger.exception("Failed to update .env")
        return jsonify({"error": f"Failed to update .env: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)






















