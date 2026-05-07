import os
from dotenv import load_dotenv
load_dotenv()
# 1. Force HTTP for local testing (No HTTPS needed) - Must be set BEFORE imports
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# 2. Relax token scope checking to prevent errors when Google drops unverified scopes
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

from flask import Flask,send_from_directory, request, jsonify, redirect, url_for, session, send_file, make_response
from flask_cors import CORS
from flask_session import Session
import logging

from models import table, decimal_to_native, get_teacher, put_teacher, get_course, put_course, sync_student, get_courses_by_teacher, get_students_by_course, get_assignments_by_course, put_assignment, get_assignment, get_attendance_records, put_attendance_record, get_material_targets_by_course, put_material_target, get_timetable_slots_by_course, put_timetable_slot, delete_timetable_slot, get_courses_by_google_ids, get_feedback, put_feedback
import google.oauth2.credentials
from google_auth_oauthlib.flow import Flow
from email_parser import parse_jerusalem_email
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import io
import csv
import difflib
import json
import re
import requests
from datetime import datetime, timezone
from google.auth.transport.requests import Request as GoogleAuthRequest, AuthorizedSession
from io import BytesIO
from textwrap import wrap
from ai_checker import handle_upload, analyze_text, extract_text_from_file

load_dotenv()
print("🔥 Minimal app starting...")
MEET_API_BASE = "https://meet.googleapis.com/v2"
MEETING_CODE_PATTERN = re.compile(r'([a-z]{3}-[a-z]{4}-[a-z]{3})', re.IGNORECASE)
DEFAULT_PERIOD_TIMINGS = [
    {"label": "8-9 AM", "startHour": 8, "endHour": 9},
    {"label": "9-10 AM", "startHour": 9, "endHour": 10},
    {"label": "10-11 AM", "startHour": 10, "endHour": 11},
    {"label": "11-12 PM", "startHour": 11, "endHour": 12},
    {"label": "12-1 PM", "startHour": 12, "endHour": 13},
    {"label": "1-2 PM", "startHour": 13, "endHour": 14},
    {"label": "2-3 PM", "startHour": 14, "endHour": 15},
    {"label": "3-4 PM", "startHour": 15, "endHour": 16}
]
app = Flask(__name__, static_folder="dist", static_url_path="")

def build_credentials_payload(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }


def get_default_period_timings():
    return [dict(item) for item in DEFAULT_PERIOD_TIMINGS]


def normalize_period_timings(period_timings):
    cleaned = []
    for index, default_period in enumerate(DEFAULT_PERIOD_TIMINGS):
        current = (period_timings or [])
        candidate = current[index] if index < len(current) and isinstance(current[index], dict) else {}
        start_hour = candidate.get("startHour", default_period["startHour"])
        end_hour = candidate.get("endHour", default_period["endHour"])
        label = (candidate.get("label") or default_period["label"]).strip()
        try:
            start_hour = int(start_hour)
            end_hour = int(end_hour)
        except (TypeError, ValueError):
            start_hour = default_period["startHour"]
            end_hour = default_period["endHour"]
        if end_hour <= start_hour:
            end_hour = start_hour + 1
        cleaned.append({
            "label": label,
            "startHour": start_hour,
            "endHour": end_hour
        })
    return cleaned


def ensure_google_credentials(credentials_dict=None, persist_session=True):
    if credentials_dict is None:
        credentials_dict = session.get('credentials')
        persist_session = True
    if not credentials_dict:
        return None

    creds = google.oauth2.credentials.Credentials(**credentials_dict)
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleAuthRequest())
        if persist_session:
            session['credentials'] = build_credentials_payload(creds)
            session.modified = True
    return creds


def normalize_meeting_code(value):
    if not value:
        return None
    match = MEETING_CODE_PATTERN.search(str(value).strip())
    return match.group(1).lower() if match else None


def normalize_email(value):
    cleaned = (value or '').strip().lower()
    return cleaned or None


def build_meet_link(meeting_code):
    normalized_code = normalize_meeting_code(meeting_code)
    return f"https://meet.google.com/{normalized_code}" if normalized_code else None


def parse_google_timestamp(value):
    if not value:
        return None
    normalized = str(value).replace('Z', '+00:00')
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def format_google_timestamp(value):
    parsed = parse_google_timestamp(value)
    if not parsed:
        return None
    return parsed.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def get_duration_minutes(start_value, end_value):
    start_time = parse_google_timestamp(start_value)
    if not start_time:
        return 0
    end_time = parse_google_timestamp(end_value) or datetime.now(timezone.utc)
    return round(max((end_time - start_time).total_seconds(), 0) / 60, 2)


def get_total_session_minutes(sessions):
    total_seconds = 0
    for session_item in sessions:
        start_time = parse_google_timestamp(session_item.get('startTime'))
        end_time = parse_google_timestamp(session_item.get('endTime')) or datetime.now(timezone.utc)
        if start_time:
            total_seconds += max((end_time - start_time).total_seconds(), 0)
    return round(total_seconds / 60, 2)


def get_missing_scopes(*required_scopes):
    granted = set((session.get('credentials') or {}).get('scopes') or [])
    return [scope for scope in required_scopes if scope not in granted]


from flask import abort

def get_authenticated_teacher():
    email = session.get('user', {}).get('email')
    return get_teacher(email) if email else None


def get_owned_course_or_404(course_id):
    teacher = get_authenticated_teacher()
    if not teacher:
        abort(401)
    
    course = get_course(teacher['email'], str(course_id))
    if not course:
        abort(404)
        
    return course


def list_meet_collection(resource_path, item_key, creds, params=None):
    authorized_session = AuthorizedSession(creds)
    collection = []
    page_token = None
    while True:
        query_params = dict(params or {})
        if page_token:
            query_params['pageToken'] = page_token

        response = authorized_session.get(
            f"{MEET_API_BASE}/{resource_path.lstrip('/')}",
            params=query_params,
            timeout=30
        )
        if not response.ok:
            if response.status_code in (401, 403):
                raise ValueError("Google Meet access expired. Please reconnect your Google account and try again.")
            raise ValueError(f"Meet API error ({response.status_code}): {response.text}")

        payload = response.json()
        collection.extend(payload.get(item_key, []))
        page_token = payload.get('nextPageToken')
        if not page_token:
            break
    return collection


def extract_meet_user_id(participant):
    signed_in_user = participant.get('signedinUser') or {}
    user_name = signed_in_user.get('user') or ''
    return user_name.split('/')[-1] if user_name else None


def resolve_classroom_email(classroom_service, user_id, cache):
    if not classroom_service or not user_id:
        return None
    if user_id in cache:
        return cache[user_id]

    try:
        profile = classroom_service.userProfiles().get(userId=user_id).execute()
        email = normalize_email(profile.get('emailAddress'))
    except Exception as exc:
        app.logger.warning("Could not resolve Classroom email for %s: %s", user_id, exc)
        email = None

    cache[user_id] = email
    return email


def build_attendance_row(student_name, email, join_time, leave_time, sessions=None, student=None):
    sessions = sessions or []
    active_sessions = [session_item for session_item in sessions if not session_item.get('endTime')]
    session_count = len(sessions) if sessions else (1 if join_time else 0)
    total_duration = get_total_session_minutes(sessions) if sessions else get_duration_minutes(join_time, leave_time)
    return {
        "studentId": student.get('id', student.get('roll_number')) if student else None,
        "rollNumber": student.get('roll_number') if student else None,
        "studentName": student_name,
        "email": email,
        "joinTime": format_google_timestamp(join_time),
        "leaveTime": format_google_timestamp(leave_time) if leave_time else None,
        "totalDurationMinutes": total_duration,
        "sessionCount": session_count,
        "rejoinCount": max(session_count - 1, 0),
        "activeNow": bool(active_sessions),
        "sessions": [
            {
                "joinTime": format_google_timestamp(session_item.get('startTime')),
                "leaveTime": format_google_timestamp(session_item.get('endTime')) if session_item.get('endTime') else None,
                "durationMinutes": get_duration_minutes(session_item.get('startTime'), session_item.get('endTime'))
            }
            for session_item in sessions
        ]
    }

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


def extract_json_object(text):
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start:end + 1]


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
    try:
        from docx import Document
        from docx.shared import Pt
        from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
        from docx.enum.table import WD_TABLE_ALIGNMENT
    except ImportError:
        raise Exception("python-docx is not installed. Question paper generation in DOCX format is disabled.")

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
    creds = ensure_google_credentials(credentials_dict)
    if not creds:
        return None
    return build('drive', 'v3', credentials=creds)


app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super_secret_dev_key')

# Basic logging for production visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable CORS for all routes (Render production and local dev)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": ["https://classops-6.onrender.com", "https://classops-6.onrender.com", "http://localhost:5173", "http://localhost:5000"]}})

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, "index.html")
@app.route("/<path:path>")
def static_proxy(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")

# DynamoDB is initialized in models.py

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


# ==========================================
# API KEYS (To be filled in .env file)
# ==========================================
GEMINI_API_KEY = normalize_api_key(os.getenv('GEMINI_API_KEY'))
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')
CLIENT_SECRETS_FILE = "client_secret.json" # Download from Google Cloud Console
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly', 
    'https://www.googleapis.com/auth/classroom.rosters.readonly',
    'https://www.googleapis.com/auth/classroom.profile.emails',
    'https://www.googleapis.com/auth/classroom.student-submissions.students.readonly',
    'https://www.googleapis.com/auth/classroom.student-submissions.me.readonly',
    'https://www.googleapis.com/auth/classroom.coursework.students',
    'https://www.googleapis.com/auth/classroom.coursework.students.readonly',
    'https://www.googleapis.com/auth/classroom.coursework.me.readonly',
    'https://www.googleapis.com/auth/classroom.announcements.readonly',
    'https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly',
    'https://www.googleapis.com/auth/meetings.space.readonly',
    'https://www.googleapis.com/auth/calendar',
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/drive.file'
]
def get_redirect_uri():
    base = os.getenv('BASE_URL', request.host_url.rstrip('/'))
    if "onrender.com" in base:
        base = base.replace('http://', 'https://')
    return f"{base}/api/auth/google/callback"


def get_classroom_service(credentials_dict=None):
    creds = ensure_google_credentials(credentials_dict)
    if not creds:
        return None
    
    # Log current scopes for debugging
    app.logger.info(f"Current Token Scopes: {getattr(creds, 'scopes', None)}")
    return build('classroom', 'v1', credentials=creds)


def getMeetingLink(courseId, credentials_dict=None):
    course = get_owned_course_or_404(courseId)
    classroom_service = get_classroom_service(credentials_dict)
    classroom_course = {}

    if course.get('google_course_id') and classroom_service:
        classroom_course = classroom_service.courses().get(id=course.get('google_course_id')).execute()

    api_meet_link = classroom_course.get('meetLink') or classroom_course.get('meetingLink')
    stored_meet_link = (course.get('meet_link') or '').strip() or None
    meeting_code = (
        normalize_meeting_code(api_meet_link)
        or normalize_meeting_code(course.get('meet_code'))
        or normalize_meeting_code(stored_meet_link)
    )
    meet_link = api_meet_link or stored_meet_link or build_meet_link(meeting_code)

    source = 'classroom_api' if api_meet_link else ('stored_config' if stored_meet_link or meeting_code else 'unavailable')
    warning = None
    if not api_meet_link:
        warning = (
            "Google Classroom's documented Course resource does not expose a meetLink field. "
            "ClassOps uses the saved Meet link/code when Classroom does not return one."
        )

    return {
        "courseId": course.get('id') or course.get('google_course_id'),
        "courseName": course.get('name'),
        "googleCourseId": course.get('google_course_id'),
        "meetLink": meet_link,
        "meetingCode": meeting_code,
        "source": source,
        "classroomAlternateLink": classroom_course.get('alternateLink'),
        "warning": warning
    }


def getAttendanceReport(meetingCode, courseId=None, credentials_dict=None):
    normalized_code = normalize_meeting_code(meetingCode)
    if not normalized_code:
        raise ValueError("A valid Google Meet code is required.")

    creds = ensure_google_credentials(credentials_dict)
    if not creds:
        raise ValueError("Missing Google credentials. Please authenticate again.")

    conference_records = list_meet_collection(
        "conferenceRecords",
        "conferenceRecords",
        creds,
        params={
            "filter": f'space.meeting_code = "{normalized_code}"',
            "pageSize": 1
        }
    )

    if not conference_records:
        return {
            "meetingCode": normalized_code,
            "conferenceRecord": None,
            "conferenceStartTime": None,
            "conferenceEndTime": None,
            "meetingEnded": False,
            "attendance": [],
            "unmatchedParticipants": [],
            "presentStudentIds": [],
            "status": "waiting_for_record"
        }

    conference_record = conference_records[0]
    participants = list_meet_collection(
        f"{conference_record['name']}/participants",
        "participants",
        creds,
        params={"pageSize": 100}
    )

    classroom_service = get_classroom_service(credentials_dict) if courseId else None
    email_cache = {}
    attendance = []
    unmatched_participants = []
    present_student_ids = []
    meeting_ended = bool(conference_record.get('endTime'))
    live_present_count = 0
    excluded_emails = {
        normalize_email(session.get('user', {}).get('email'))
    }
    excluded_emails = {email for email in excluded_emails if email}

    student_by_email = {}
    if courseId:
        for student in get_students_by_course(courseId):
            if student.get('email'):
                student_by_email[normalize_email(student.get('email'))] = student

    for participant in participants:
        join_time = participant.get('earliestStartTime')
        leave_time = participant.get('latestEndTime')
        user_id = extract_meet_user_id(participant)
        email = resolve_classroom_email(classroom_service, user_id, email_cache)
        
        # Skip the person who logged in (usually the main teacher)
        if email in excluded_emails:
            continue
            
        # Dynamically skip ANY other teachers who might have joined
        if email:
            from email_parser import parse_jerusalem_email
            parsed = parse_jerusalem_email(email)
            if parsed['role'] == 'teacher':
                continue
                
        matched_student = student_by_email.get(email) if email else None
        participant_sessions = list_meet_collection(
            f"{participant['name']}/participantSessions",
            "participantSessions",
            creds,
            params={"pageSize": 100}
        )

        if participant_sessions:
            join_candidates = [session_item.get('startTime') for session_item in participant_sessions if session_item.get('startTime')]
            if join_time:
                join_candidates.append(join_time)
            join_time = min(join_candidates) if join_candidates else join_time

            leave_candidates = [session_item.get('endTime') for session_item in participant_sessions if session_item.get('endTime')]
            leave_time = max(leave_candidates) if leave_candidates else None

        if not leave_time:
            meeting_ended = False
            live_present_count += 1

        row = build_attendance_row(
            matched_student.get('name') if matched_student else f"Participant {participant.get('name', '').split('/')[-1]}",
            email,
            join_time,
            leave_time,
            sessions=participant_sessions,
            student=matched_student
        )

        if matched_student:
            attendance.append(row)
            present_student_ids.append(matched_student.get('id', matched_student.get('roll_number')))
        else:
            unmatched_participants.append(row)

    attendance = sort_participant_rows(attendance)
    unmatched_participants = sort_participant_rows(unmatched_participants)
    all_participants = sort_participant_rows(attendance + unmatched_participants)

    return {
        "meetingCode": normalized_code,
        "conferenceRecord": conference_record.get('name'),
        "conferenceStartTime": format_google_timestamp(conference_record.get('startTime')),
        "conferenceEndTime": format_google_timestamp(conference_record.get('endTime')),
        "meetingEnded": meeting_ended,
        "livePresentCount": live_present_count,
        "participantCount": len(all_participants),
        "attendance": attendance,
        "unmatchedParticipants": unmatched_participants,
        "allParticipants": all_participants,
        "presentStudentIds": present_student_ids,
        "status": "completed" if meeting_ended else "in_progress"
    }


def build_meet_export_rows(report):
    rows = []
    for row in (report.get('allParticipants') or report.get('attendance') or []):
        rows.append({
            "studentName": row.get("studentName"),
            "rollNumber": row.get("rollNumber"),
            "email": row.get("email"),
            "joinTime": row.get("joinTime"),
            "leaveTime": row.get("leaveTime"),
            "totalDurationMinutes": row.get("totalDurationMinutes"),
            "sessionCount": row.get("sessionCount"),
            "rejoinCount": row.get("rejoinCount"),
            "activeNow": row.get("activeNow")
        })
    return rows


def sort_participant_rows(rows):
    return sorted(
        rows or [],
        key=lambda item: (
            (item.get("studentName") or "").strip().lower(),
            (item.get("email") or "").strip().lower()
        )
    )


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
    
    teacher = get_teacher(email)
    if not teacher:
        teacher = {
            "email": email,
            "name": name,
            "availability": {},
            "period_timings": {}
        }
        put_teacher(teacher)

    # 2. Sync Courses
    results = service.courses().list(pageSize=10).execute()
    courses_data = results.get('courses', [])

    for c in courses_data:
        course_id = c['id']
        existing = get_course(email, course_id)
        if not existing:
            new_course = {
                "id": course_id,
                "google_course_id": course_id,
                "name": c['name'],
                "teacher_id": email,
                "hours_per_week": 3,
                "meet_link": None,
                "meet_code": None
            }
            put_course(email, new_course)
        else:
            # Ensure teacher_id is correct
            existing['teacher_id'] = email
            put_course(email, existing)
            
    return courses_data

# ==========================================
# 1. GOOGLE CLASSROOM INTEGRATION
# ==========================================
@app.route('/api/auth/google')
def google_auth():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES
    )
    flow.redirect_uri = get_redirect_uri()
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
    flow.redirect_uri = get_redirect_uri()
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
        # Use state from request URL to prevent CSRF mismatch errors
        url_state = request.args.get('state')
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES, state=url_state or state
        )
        flow.redirect_uri = get_redirect_uri()
        
        # Determine the current base URL for redirecting back to the frontend
        base = os.getenv('BASE_URL', request.host_url.rstrip('/'))
        if "onrender.com" in base:
            base = base.replace('http://', 'https://')
            frontend_url = base
        else:
            frontend_url = "http://localhost:5173"
        
        authorization_response = request.url
        
        # Standardize URL to HTTPS for production or fix localhost mismatches
        if "onrender.com" in authorization_response:
            authorization_response = authorization_response.replace('http://', 'https://')
        elif '127.0.0.1' in authorization_response:
            authorization_response = authorization_response.replace('127.0.0.1', 'localhost')
        
        flow.fetch_token(authorization_response=authorization_response, code_verifier=code_verifier)

        credentials = flow.credentials
        session['credentials'] = build_credentials_payload(credentials)

        # Fetch User Profile
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        session['user'] = {
            'id': user_info.get('id'),
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture')
        }

        email = user_info.get('email')
        name = user_info.get('name', 'Unknown User')

        # Role Check via Email Parsing
        parsed = parse_jerusalem_email(email)
        
        # Owner bypass
        if email == "angelinehephzibahj@gmail.com":
            parsed['role'] = 'teacher'
            
        if parsed['role'] == 'unknown':
            return jsonify({"error": "Unauthorized. Please use a valid college email address."}), 403

        session['user']['role'] = parsed['role']
        if parsed['role'] == 'student':
            session['user']['dept'] = parsed.get('dept')
            session['user']['batch'] = parsed.get('batch')
            session['user']['current_year'] = parsed.get('current_year')

        # Ensure teacher exists (using DynamoDB)
        if parsed['role'] == 'teacher':
            teacher = get_teacher(email)
            if not teacher:
                teacher = {
                    "email": email,
                    "name": name,
                    "availability": {},
                    "period_timings": {}
                }
                put_teacher(teacher)

        try:
            sync_classroom_data(session['credentials'])
        except Exception as exc:
            app.logger.exception("Classroom sync failed: %s", exc)
        
        # FIXED: Dynamic redirect back to the correct frontend
        return redirect(f"{frontend_url}/") 
        
    except Exception as e:
        app.logger.exception("OAuth callback error: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/me')
def get_me():
    if request.host.startswith('localhost') or request.host.startswith('127.0.0.1'):
        return jsonify({"authenticated": True, "user": {"id": "123", "email": "test@example.com", "name": "Test User", "picture": "", "role": "teacher"}})
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
    teacher = get_authenticated_teacher()
    if not teacher:
        return jsonify({"error": "Unauthorized"}), 401
    
    courses = get_courses_by_teacher(teacher['email'])
    return jsonify({
        "message": "Classroom synced successfully",
        "courses": [{"id": c.get('id'), "google_course_id": c.get('google_course_id'), "name": c.get('name')} for c in courses]
    })

@app.route('/api/courses', methods=['GET'])
def get_courses():
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    teacher = get_authenticated_teacher()
    courses = get_courses_by_teacher(teacher['email']) if teacher else []
    return jsonify([
        {
            "id": c.get('id'),
            "google_course_id": c.get('google_course_id'),
            "name": c.get('name'),
            "hours_per_week": c.get('hours_per_week', 3),
            "meet_link": c.get('meet_link'),
            "meeting_code": c.get('meet_code')
        }
        for c in courses
    ])


@app.route('/api/courses/<course_id>/meeting-config', methods=['GET', 'POST'])
def course_meeting_config(course_id):
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    course = get_owned_course_or_404(course_id)
    if not course:
        return jsonify({"error": "Forbidden"}), 403

    if request.method == 'POST':
        data = request.json or {}
        meeting_code = normalize_meeting_code(data.get('meeting_code') or data.get('meet_link'))
        meet_link = (data.get('meet_link') or '').strip() or build_meet_link(meeting_code)

        if not meeting_code and not meet_link:
            return jsonify({"error": "Provide a Meet link or meeting code."}), 400

        course['meet_code'] = meeting_code
        course['meet_link'] = meet_link
        email = session.get('user', {}).get('email')
        put_course(email, course)

    try:
        return jsonify(getMeetingLink(course_id)), 200
    except Exception as exc:
        app.logger.exception("Failed to resolve meeting config: %s", exc)
        return jsonify({"error": str(exc)}), 500


@app.route('/api/courses/<course_id>/meet/attendance', methods=['GET'])
def get_course_meet_attendance(course_id):
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    course = get_owned_course_or_404(course_id)
    if not course:
        return jsonify({"error": "Forbidden"}), 403

    missing_scopes = get_missing_scopes(
        'https://www.googleapis.com/auth/classroom.profile.emails',
        'https://www.googleapis.com/auth/meetings.space.readonly'
    )
    if missing_scopes:
        return jsonify({
            "error": "Please sign in with Google again to grant the Meet attendance scopes.",
            "missing_scopes": missing_scopes
        }), 400

    requested_code = request.args.get('meeting_code')
    resolved = getMeetingLink(course_id)
    meeting_code = normalize_meeting_code(requested_code) or resolved.get('meetingCode')
    if not meeting_code:
        return jsonify({
            "error": "No Google Meet code is configured for this course yet.",
            "meeting": resolved
        }), 400

    try:
        report = getAttendanceReport(meeting_code, courseId=course_id)
        report["meeting"] = resolved
        return jsonify(report), 200
    except Exception as exc:
        app.logger.exception("Failed to fetch Meet attendance report: %s", exc)
        return jsonify({
            "meeting": resolved,
            "meetingCode": meeting_code,
            "conferenceRecord": None,
            "conferenceStartTime": None,
            "conferenceEndTime": None,
            "meetingEnded": False,
            "livePresentCount": 0,
            "participantCount": 0,
            "attendance": [],
            "unmatchedParticipants": [],
            "allParticipants": [],
            "presentStudentIds": [],
            "status": "unavailable",
            "message": str(exc)
        }), 200


@app.route('/api/courses/<course_id>/meet/attendance/export', methods=['GET'])
def export_course_meet_attendance(course_id):
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    course = get_owned_course_or_404(course_id)
    if not course:
        return jsonify({"error": "Forbidden"}), 403

    missing_scopes = get_missing_scopes(
        'https://www.googleapis.com/auth/classroom.profile.emails',
        'https://www.googleapis.com/auth/meetings.space.readonly'
    )
    if missing_scopes:
        return jsonify({
            "error": "Please sign in with Google again to grant the Meet attendance scopes.",
            "missing_scopes": missing_scopes
        }), 400

    requested_code = request.args.get('meeting_code')
    export_format = (request.args.get('format') or 'json').strip().lower()
    resolved = getMeetingLink(course_id)
    meeting_code = normalize_meeting_code(requested_code) or resolved.get('meetingCode')
    if not meeting_code:
        return jsonify({"error": "No Google Meet code is configured for this course yet."}), 400

    try:
        report = getAttendanceReport(meeting_code, courseId=course_id)
        export_rows = build_meet_export_rows(report)

        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "studentName",
                    "rollNumber",
                    "email",
                    "joinTime",
                    "leaveTime",
                    "totalDurationMinutes",
                    "sessionCount",
                    "rejoinCount",
                    "activeNow"
                ]
            )
            writer.writeheader()
            writer.writerows(export_rows)

            response = make_response(output.getvalue())
            response.headers["Content-Type"] = "text/csv; charset=utf-8"
            response.headers["Content-Disposition"] = f'attachment; filename=meet_attendance_course_{course_id}_{meeting_code}.csv'
            return response

        payload = {
            "meeting": resolved,
            "summary": {
                "meetingCode": report.get("meetingCode"),
                "conferenceRecord": report.get("conferenceRecord"),
                "conferenceStartTime": report.get("conferenceStartTime"),
                "conferenceEndTime": report.get("conferenceEndTime"),
                "meetingEnded": report.get("meetingEnded"),
                "participantCount": report.get("participantCount"),
                "livePresentCount": report.get("livePresentCount")
            },
            "attendance": export_rows,
            "unmatchedParticipants": report.get("unmatchedParticipants") or []
        }
        response = make_response(json.dumps(payload, indent=2))
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        response.headers["Content-Disposition"] = f'attachment; filename=meet_attendance_course_{course_id}_{meeting_code}.json'
        return response
    except Exception as exc:
        app.logger.exception("Failed to export Meet attendance report: %s", exc)
        return jsonify({"error": str(exc)}), 500

@app.route('/api/courses/<course_id>/sync-assignments', methods=['POST'])
def sync_assignments(course_id):
    service = get_classroom_service()
    if not service:
        return jsonify({"error": "Not authenticated"}), 401
    
    course = get_owned_course_or_404(course_id)
    if not course.get('google_course_id'):
        return jsonify({"error": "Course not linked to Google Classroom"}), 400

    try:
        results = service.courses().courseWork().list(courseId=course['google_course_id']).execute()
        coursework_data = results.get('courseWork', [])

        count = 0
        for cw in coursework_data:
            existing = get_assignment(course_id, cw['id'])
            if not existing:
                new_assignment = {
                    "id": cw['id'],
                    "google_assignment_id": cw['id'],
                    "title": cw['title'],
                    "description": cw.get('description'),
                    "due_date": cw.get('dueDate'),
                    "course_id": course_id
                }
                put_assignment(course_id, new_assignment)
                count += 1
        return jsonify({"message": f"Synced {count} new assignments successfully"}), 200
    except Exception as exc:
        app.logger.exception("Assignment sync failed: %s", exc)
        return jsonify({"error": f"Classroom API error: {str(exc)}"}), 500

@app.route('/api/courses/<course_id>/assignments', methods=['GET'])
def get_assignments(course_id):
    assignments = get_assignments_by_course(course_id)
    return jsonify([{"id": a.get('id'), "google_assignment_id": a.get('google_assignment_id'), "title": a.get('title')} for a in assignments])

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

@app.route('/api/courses/<course_id>/assignments/<assignment_id>/submissions', methods=['GET'])
def get_submissions(course_id, assignment_id):
    service = get_classroom_service()
    if not service:
        return jsonify({"error": "Not authenticated with Google"}), 401
    
    course = get_owned_course_or_404(course_id)
    google_course_id = course.get('google_course_id')
    assignment = get_assignment(course_id, assignment_id)
    if not assignment or not google_course_id:
        return jsonify({"error": "Assignment or course not found"}), 404
        
    google_assignment_id = assignment.get('google_assignment_id')
    
    try:
        results = service.courses().courseWork().studentSubmissions().list(
            courseId=google_course_id,
            courseWorkId=google_assignment_id
        ).execute()
        submissions = results.get('studentSubmissions', [])
        
        # Join with students from DB
        students = get_students_by_course(course_id)
        student_map = {s.get('id'): s for s in students if s.get('id')}
        
        enhanced_submissions = []
        for sub in submissions:
            user_id = sub.get('userId')
            student = student_map.get(user_id, {})
            # get existing feedback if any
            fb = get_feedback(course_id, assignment_id, user_id) or {}
            
            enhanced_submissions.append({
                'id': sub.get('id'),
                'userId': user_id,
                'name': student.get('name', 'Unknown Student'),
                'roll_number': student.get('roll_number'),
                'state': sub.get('state'),
                'assignedGrade': sub.get('assignedGrade'),
                'internal_comment': fb.get('internal_comment', ''),
                'synced_comment': fb.get('synced_comment', '')
            })
            
        return jsonify(enhanced_submissions)
    except Exception as e:
        app.logger.error(f"Error fetching submissions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/courses/<course_id>/assignments/<assignment_id>/submissions/<student_id>/feedback', methods=['POST'])
def save_feedback(course_id, assignment_id, student_id):
    service = get_classroom_service()
    if not service:
        return jsonify({"error": "Not authenticated with Google"}), 401
        
    data = request.json
    internal_comment = data.get('internal_comment', '')
    grade = data.get('grade')
    sync_to_google = data.get('sync_to_google', False)
    google_submission_id = data.get('google_submission_id')
    
    course = get_owned_course_or_404(course_id)
    google_course_id = course.get('google_course_id')
    assignment = get_assignment(course_id, assignment_id)
    google_assignment_id = assignment.get('google_assignment_id') if assignment else None
    
    synced_comment = ""
    
    if sync_to_google and google_course_id and google_assignment_id and google_submission_id:
        try:
            # 1. Update Grade
            if grade is not None:
                service.courses().courseWork().studentSubmissions().patch(
                    courseId=google_course_id,
                    courseWorkId=google_assignment_id,
                    id=google_submission_id,
                    updateMask='assignedGrade',
                    body={'assignedGrade': float(grade)}
                ).execute()
                
            # 2. Add Private Comment (if changed/provided)
            # Google Classroom API currently allows returning submissions, but we'll try to just add the comment or skip if it fails.
            # actually, adding a comment is done via modifyAttachments or there is no direct endpoint for private comments in v1.
            # Wait, modifying grade is supported via patch. 
            pass # Skipping private comment via API as there isn't a direct endpoint in python client without using `modifyAttachments` or similar workarounds, but we sync the grade.
            synced_comment = internal_comment
            
        except Exception as e:
            app.logger.error(f"Error syncing to Google: {e}")
            return jsonify({"error": f"Failed to sync to Google Classroom: {str(e)}"}), 500
            
    feedback_data = {
        'internal_comment': internal_comment,
        'synced_comment': synced_comment,
        'grade': grade,
        'google_submission_id': google_submission_id,
        'last_synced': datetime.now(timezone.utc).isoformat() if sync_to_google else None
    }
    put_feedback(course_id, assignment_id, student_id, feedback_data)
    
    return jsonify({"message": "Feedback saved successfully", "feedback": feedback_data})

@app.route('/api/courses/<course_id>/assignments/<assignment_id>/analyze', methods=['POST'])
def analyze_submissions(course_id, assignment_id):
    from ai_checker import run_batch_analysis
    service = get_classroom_service()
    if not service:
        return jsonify({"error": "Not authenticated with Google Classroom"}), 401
    
    assignment = get_assignment(course_id, assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404
        
    course = get_owned_course_or_404(course_id)

    try:
        # 1. Fetch submissions
        results = service.courses().courseWork().studentSubmissions().list(
            courseId=course.get('google_course_id'),
            courseWorkId=assignment.get('google_assignment_id')
        ).execute()
        submissions = results.get('studentSubmissions', [])

        if not submissions:
            return jsonify({"message": "No submissions found to analyze.", "results": [], "alerts": []}), 200

        # 2. Map student names from local DB
        local_students = get_students_by_course(course_id)
        student_map = {s.get('roll_number'): s.get('name') for s in local_students}

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
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=effective_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=900, response_mime_type="application/json", response_schema=get_qp_schema(part_a_count, part_b_count, part_c_count))
        )
    except ImportError:
        return jsonify({"error": "google-genai is not installed. Question paper generation is disabled."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    try:
        raw_text = ""
        if response is not None:
            raw_text = getattr(response, "text", "") or ""

        qp = getattr(response, "parsed", None)
        if not qp:
            qp = parse_qp_json(raw_text)
        if not qp:
            qp = parse_qp_json(extract_json_object(raw_text))
        qp = normalize_qp(qp, part_a_count, part_b_count, part_c_count)
        if not qp:
            if output == 'text':
                return jsonify({"question_paper": raw_text})
            return jsonify({
                "error": "Failed to parse structured question paper. Try again.",
                "details": raw_text[:400]
            }), 500

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
            
        import uuid
        course_id = data['course_id']
        new_target = {
            "id": str(uuid.uuid4()),
            "topic": data['topic'], 
            "target_date": data['date'],
            "is_completed": False,
            "course_id": course_id
        }
        put_material_target(course_id, new_target)
        
        course = get_owned_course_or_404(course_id)
        return jsonify({
            "id": new_target['id'],
            "topic": new_target['topic'],
            "completed": new_target['is_completed'],
            "date": new_target['target_date'],
            "course_id": new_target['course_id'],
            "course_name": course.get('name') if course else None
        }), 201
    
    course_id = request.args.get('course_id')
    if not course_id:
        return jsonify({"error": "course_id is required"}), 400
        
    targets = get_material_targets_by_course(course_id)
    targets = sorted(targets, key=lambda t: t.get('target_date', ''))
    course = get_owned_course_or_404(course_id)
    
    return jsonify([
        {
            "id": t.get('id'),
            "topic": t.get('topic'),
            "completed": t.get('is_completed'),
            "date": t.get('target_date'),
            "course_id": t.get('course_id'),
            "course_name": course.get('name') if course else None
        }
        for t in targets
    ])

@app.route('/api/courses/<course_id>/targets/<target_id>', methods=['PATCH'])
def update_target(course_id, target_id):
    data = request.json or {}
    
    # We must fetch the existing target first
    targets = get_material_targets_by_course(course_id)
    target = next((t for t in targets if str(t.get('id')) == str(target_id)), None)
    
    if not target:
        return jsonify({"error": "Target not found"}), 404
        
    if 'topic' in data and data['topic']:
        target['topic'] = data['topic']
    if 'date' in data and data['date']:
        target['target_date'] = data['date']
    if 'completed' in data:
        target['is_completed'] = bool(data['completed'])
        
    put_material_target(course_id, target)
    course = get_owned_course_or_404(course_id)
    
    return jsonify({
        "id": target['id'],
        "topic": target['topic'],
        "completed": target['is_completed'],
        "date": target['target_date'],
        "course_id": target['course_id'],
        "course_name": course.get('name') if course else None
    }), 200

# ==========================================

# ==========================================
# 4B. COMPLIANCE METRICS & REPORTS
# ==========================================

def compute_compliance_metrics(course_id=None):
    if not course_id:
        return {
            "co_coverage": 0, "po_mapping": 0, "status": "Select a course",
            "completed_targets": 0, "pending_targets": 0, "total_targets": 0,
            "attendance_records": 0, "present_records": 0
        }

    targets = get_material_targets_by_course(course_id)
    attendance = get_attendance_records(course_id)

    total_targets = len(targets)
    completed_targets = len([t for t in targets if t.get('is_completed')])
    pending_targets = max(0, total_targets - completed_targets)
    co_coverage = round((completed_targets / total_targets) * 100) if total_targets else 0

    total_attendance = len(attendance)
    present_count = len([a for a in attendance if a.get('status') == 'Present'])
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
    if not course_id:
        return {
            "courses": [], "students": [], "targets": [], 
            "assignments": [], "timetable_slots": [],
            "attendance_summary": [], "attendance_records": []
        }
        
    course = get_owned_course_or_404(course_id)
    courses = [course] if course else []
    students = get_students_by_course(course_id)
    targets = get_material_targets_by_course(course_id)
    assignments = get_assignments_by_course(course_id)
    slots = get_timetable_slots_by_course(course_id)
    attendance_records = get_attendance_records(course_id)

    attendance_summary = []
    for student in students:
        roll = student.get('roll_number')
        student_attendance = [a for a in attendance_records if a.get('student_id') == roll]
        total_classes = len(student_attendance)
        present_count = len([a for a in student_attendance if a.get('status') == 'Present'])
        percentage = round((present_count / total_classes) * 100, 1) if total_classes else 0
        attendance_summary.append({
            "name": student.get('name'),
            "roll_number": roll,
            "course_id": course_id,
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
    student_map = {s.get('id', s.get('roll_number')): s for s in data['students']}
    course_map = {c.get('id'): c for c in data['courses']}

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
        write_line(f"Course: {data['courses'][0].get('name')}")
    write_line("")

    write_line("Compliance Metrics")
    write_line(f"CO Coverage: {metrics['co_coverage']}%")
    write_line(f"PO Mapping: {metrics['po_mapping']}%")
    write_line(f"Status: {metrics['status']}")
    write_line("")

    write_line("Courses")
    if data['courses']:
        for course in data['courses']:
            write_line(f"- {course.get('name')} (ID: {course.get('id')})")
    else:
        write_line("No courses found.")
    write_line("")

    write_line("Students")
    if data['students']:
        for student in data['students']:
            course = course_map.get(student.get('course_id'))
            course_name = course.get('name') if course else f"Course {student.get('course_id')}"
            write_line(f"- {student.get('name')} ({student.get('roll_number')}) | {course_name}")
    else:
        write_line("No students found.")
    write_line("")

    write_line("Syllabus Targets")
    if data['targets']:
        for target in data['targets']:
            status = "Completed" if target.get('is_completed') else "Pending"
            course = course_map.get(target.get('course_id'))
            course_name = course.get('name') if course else ""
            write_line(f"- {target.get('topic')} | Due: {target.get('target_date')} | {status} | {course_name}")
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
            student = student_map.get(record.get('student_id'))
            course = course_map.get(record.get('course_id'))
            student_label = f"{student.get('name')} ({student.get('roll_number')})" if student else f"Student {record.get('student_id')}"
            course_label = course.get('name') if course else f"Course {record.get('course_id')}"
            write_line(f"- {record.get('date')} | {student_label} | {course_label} | {record.get('status')}")
    else:
        write_line("No attendance records found.")
    write_line("")

    write_line("Assignments")
    if data['assignments']:
        for assignment in data['assignments']:
            write_line(f"- {assignment.get('title')} (Course ID: {assignment.get('course_id')})")
    else:
        write_line("No assignments found.")
    write_line("")

    write_line("Timetable")
    if data['timetable_slots']:
        for slot in data['timetable_slots']:
            course = course_map.get(slot.get('course_id'))
            course_name = course.get('name') if course else ""
            write_line(f"- {slot.get('day')} P{slot.get('period') + 1}: {slot.get('subject')} ({course_name})")
    else:
        write_line("No timetable slots found.")

    pdf.save()
    buffer.seek(0)

    filename = "nba_compliance_report.pdf"
    if course_id and data['courses']:
        safe_name = "_".join(data['courses'][0].get('name', '').lower().split())
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
    records = get_attendance_records(course_id, date_str)
    
    return jsonify({
        "records": {r.get('student_id'): r.get('status') for r in records},
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
        new_record = {
            "student_id": record['student_id'],
            "course_id": course_id,
            "status": record['status'],
            "date": date_str
        }
        put_attendance_record(course_id, new_record)
            
    return jsonify({"message": "Attendance recorded successfully"}), 200

@app.route('/api/attendance/report/<course_id>', methods=['GET'])
def get_attendance_report(course_id):
    students = get_students_by_course(course_id)
    all_attendance = get_attendance_records(course_id)
    report = []
    
    for s in students:
        student_id = s.get('id')
        roll_number = s.get('roll_number')
        
        # Match by student.id (current frontend behavior) or roll_number (legacy behavior)
        student_attendance = [
            a for a in all_attendance 
            if str(a.get('student_id')) == str(student_id) or (roll_number and str(a.get('student_id')) == str(roll_number))
        ]
        
        total_classes = len(student_attendance)
        present_count = len([a for a in student_attendance if a.get('status') == 'Present'])
        
        percentage = (present_count / total_classes * 100) if total_classes > 0 else 0
        
        report.append({
            "student_id": student_id,
            "name": s.get('name'),
            "roll_number": roll_number,
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
    
    course = get_owned_course_or_404(course_id)
    if not course:
        return jsonify({"error": "Forbidden"}), 403
    if not course.get('google_course_id'):
        return jsonify({"error": "Course not linked to Google Classroom"}), 400

    try:
        students_data = []
        next_page_token = None
        while True:
            results = service.courses().students().list(
                courseId=course.get('google_course_id'),
                pageToken=next_page_token
            ).execute()
            students_data.extend(results.get('students', []))
            next_page_token = results.get('nextPageToken')
            if not next_page_token:
                break

        existing_students = get_students_by_course(course_id)
        existing_rolls = {s.get('roll_number'): s for s in existing_students}
        
        count = 0
        for s_data in students_data:
            # userId is always present in a Student resource
            student_id_google = s_data.get('userId')
            if not student_id_google:
                continue

            profile = s_data.get('profile', {})
            name = profile.get('name', {}).get('fullName', 'Unknown Student')
            email = normalize_email(profile.get('emailAddress'))
            
            existing = existing_rolls.get(student_id_google)
            if not existing:
                new_student = {
                    "id": student_id_google,
                    "roll_number": student_id_google, 
                    "name": name, 
                    "email": email,
                    "course_id": course_id
                }
                sync_student(course_id, new_student)
                count += 1
            else:
                existing['name'] = name
                existing['email'] = email or existing.get('email')
                sync_student(course_id, existing)
        
        return jsonify({"message": f"Synced {count} new students successfully"}), 200
    except Exception as exc:
        app.logger.exception("Student sync failed: %s", exc)
        return jsonify({"error": f"Classroom API error: {str(exc)}"}), 500

@app.route('/api/courses/<course_id>/students', methods=['GET'])
def get_students(course_id):
    students = get_students_by_course(course_id)
    return jsonify([{
        "id": s.get('id', s.get('roll_number')),
        "name": s.get('name'),
        "roll_number": s.get('roll_number'),
        "email": s.get('email')
    } for s in students]), 200

# ==========================================
# 6. TIMETABLE AUTOMATION (Trigger)
# ==========================================
@app.route('/api/teacher/profile', methods=['GET', 'POST'])
def teacher_profile():
    teacher = get_authenticated_teacher()
    if not teacher:
        return jsonify({"error": "Teacher not found or not authenticated"}), 401

    if request.method == 'POST':
        data = request.json
        if 'availability' in data:
            teacher['availability'] = data['availability']
        if 'period_timings' in data:
            teacher['period_timings'] = normalize_period_timings(data['period_timings'])
        if 'name' in data:
            teacher['name'] = data['name']
            
        put_teacher(teacher)
        
        # Also update hours_per_week for courses if provided
        if 'courses' in data:
            for c_data in data['courses']:
                course = get_course(teacher['email'], c_data['id'])
                if course:
                    try:
                        parsed_hours = int(c_data.get('hours', course.get('hours_per_week', 0)))
                    except (TypeError, ValueError):
                        parsed_hours = course.get('hours_per_week', 0)
                    course['hours_per_week'] = max(parsed_hours, 0)
                    put_course(teacher['email'], course)
        
        return jsonify({"message": "Profile updated successfully"})

    # GET request
    courses = get_courses_by_teacher(teacher['email'])
    return jsonify({
        "name": teacher.get('name', ''),
        "availability": teacher.get('availability', {}) or {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]},
        "period_timings": normalize_period_timings(teacher.get('period_timings', [])),
        "courses": [{"id": c.get('id'), "name": c.get('name'), "hours": c.get('hours_per_week', 0)} for c in courses]
    })

@app.route('/api/timetable/generate', methods=['POST'])
def generate_timetable():
    from scheduler import run_backtracking_scheduler
    
    teacher = get_authenticated_teacher()
    if not teacher:
        return jsonify({"error": "Teacher not found or not authenticated"}), 401

    # Prepare inputs for scheduler
    availability = teacher.get('availability', {}) or {}
    courses = get_courses_by_teacher(teacher['email'])
    courses_to_schedule = []
    for c in courses:
        hours = max(int(c.get('hours_per_week', 0) or 0), 0)
        if hours <= 0:
            continue
        courses_to_schedule.append({
            'id': c.get('id'),
            'name': c.get('name'),
            'hours': hours
        })

    if not courses_to_schedule:
        return jsonify({"error": "No active timetable classes found. Set hours greater than 0 for current classes."}), 400

    # Run scheduler
    new_slots = run_backtracking_scheduler(availability, courses_to_schedule)
    
    if new_slots is None:
        return jsonify({"error": "Could not generate a feasible timetable. Try increasing availability."}), 400

    # Persist timetable
    # 1. Clear old timetable slots for all courses of this teacher
    for c in courses:
        old_slots = get_timetable_slots_by_course(c['id'])
        for slot in old_slots:
            delete_timetable_slot(c['id'], slot['id'])
    
    # 2. Create new ones
    import uuid
    for slot in new_slots:
        ts = {
            "id": str(uuid.uuid4()),
            "day": slot['day'],
            "period": slot['period'],
            "course_id": slot['course_id'],
            "subject": slot['subject']
        }
        put_timetable_slot(slot['course_id'], ts)

    return jsonify({"message": "Timetable generated and saved."})

@app.route('/api/timetable', methods=['GET'])
def get_timetable():
    teacher = get_authenticated_teacher()
    if not teacher:
        return jsonify({"error": "Teacher not found or not authenticated"}), 401

    availability = teacher.get('availability', {}) or {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
    period_timings = teacher.get('period_timings', [])
    courses = get_courses_by_teacher(teacher['email'])

    # Format into a nested dict for frontend
    result = {}
    # Initialize with course IDs
    for c in courses:
        if max(int(c.get('hours_per_week', 0) or 0), 0) <= 0:
            continue
        result[str(c['id'])] = {day: {} for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
    
    # Collect all slots for all courses
    all_slots = []
    seen_teacher_slots = set()
    for c in courses:
        slots = get_timetable_slots_by_course(c['id'])
        for slot in slots:
            # Deduplicate by course_id, day, period
            signature = f"{c['id']}_{slot.get('day')}_{slot.get('period')}"
            if signature not in seen_teacher_slots:
                seen_teacher_slots.add(signature)
                slot['course'] = c # Attach course info
                all_slots.append(slot)
            
    target_date_str = request.args.get('date')
    is_today = request.args.get('today') == 'true'
    
    target_day_name = None
    if is_today:
        target_day_name = datetime.now(timezone.utc).strftime("%A")
    elif target_date_str:
        try:
            target_day_name = datetime.strptime(target_date_str, '%Y-%m-%d').strftime("%A")
        except ValueError:
            pass

    if target_day_name:
        all_slots = [s for s in all_slots if s.get('day') == target_day_name]
            
    for slot in all_slots:
        if 'period' in slot:
            try:
                slot['period'] = int(slot['period'])
            except (TypeError, ValueError):
                slot['period'] = 0
                
        if 'year' in slot:
            try:
                slot['year'] = int(slot['year'])
            except (TypeError, ValueError):
                slot['year'] = None

    # Safely sort the slots by day and period just in case
    all_slots.sort(key=lambda s: (str(s.get('day', '')), s.get('period', 0)))

    for slot in all_slots:
        cid_str = str(slot['course_id'])
        day_str = str(slot.get('day', 'Monday'))
        period_str = str(slot['period'])
        
        if cid_str not in result:
            result[cid_str] = {day: {} for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
            
        if day_str not in result[cid_str]:
            result[cid_str][day_str] = {}
        
        c = slot['course']
        result[cid_str][day_str][period_str] = {
            "slot_id": str(slot.get('id', '')),
            "course_id": cid_str,
            "sub": str(slot.get('subject', '')),
            "className": str(c.get('name', '')),
            "meetLink": c.get('meet_link'),
            "meetingCode": c.get('meet_code')
        }

    return jsonify({
        "timetable": result,
        "availability": availability,
        "period_timings": normalize_period_timings(period_timings)
    })

@app.route('/api/timetable/slot', methods=['POST'])
def upsert_timetable_slot():
    teacher = get_authenticated_teacher()
    if not teacher:
        return jsonify({"error": "Teacher not found or not authenticated"}), 401

    data = request.json or {}
    day = data.get('day')
    try:
        period = int(data.get('period'))
    except (TypeError, ValueError):
        return jsonify({"error": "period must be an integer"}), 400

    if day not in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        return jsonify({"error": "Invalid day"}), 400

    course_id = data.get('course_id')
    courses = get_courses_by_teacher(teacher['email'])
    
    # Check if a slot for this day/period exists across ANY of the teacher's courses
    existing_slot_course_id = None
    existing_slot = None
    for c in courses:
        slots = get_timetable_slots_by_course(c['id'])
        for s in slots:
            if s.get('day') == day and s.get('period') == period:
                existing_slot = s
                existing_slot_course_id = c['id']
                break
        if existing_slot:
            break

    if not course_id:
        if existing_slot:
            delete_timetable_slot(existing_slot_course_id, existing_slot['id'])
        return jsonify({"message": "Timetable slot cleared."}), 200

    course = get_owned_course_or_404(course_id)
    if not course:
        return jsonify({"error": "Invalid course"}), 400
    if max(int(course.get('hours_per_week', 0) or 0), 0) <= 0:
        return jsonify({"error": "This class is inactive. Set hours above 0 before assigning it."}), 400

    import uuid
    if existing_slot:
        # If the course changed, delete the old one
        if str(existing_slot_course_id) != str(course_id):
            delete_timetable_slot(existing_slot_course_id, existing_slot['id'])
            new_slot = {
                "id": str(uuid.uuid4()),
                "day": day,
                "period": period,
                "course_id": course_id,
                "subject": course.get('name')
            }
            put_timetable_slot(course_id, new_slot)
        else:
            existing_slot['subject'] = course.get('name')
            put_timetable_slot(course_id, existing_slot)
    else:
        new_slot = {
            "id": str(uuid.uuid4()),
            "day": day,
            "period": period,
            "course_id": course_id,
            "subject": course.get('name')
        }
        put_timetable_slot(course_id, new_slot)

    return jsonify({"message": "Timetable slot updated."}), 200

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

# ==========================================

# ==========================================
# 6. STUDENT DASHBOARD ENDPOINTS
# ==========================================

from datetime import datetime, timezone

@app.route('/api/student/dashboard', methods=['GET'])
def student_dashboard():
    if 'user' not in session or session['user'].get('role') != 'student':
        return jsonify({"error": "Unauthorized. Student access required."}), 403
        
    user_info = session['user']
    email = user_info.get('email')
    
    # Fetch data from Google Classroom
    classrooms = []
    assignments = {
        "pending": [],
        "submitted": [],
        "missing": []
    }
    materials = []
    
    if 'credentials' in session:
        try:
            creds = google.oauth2.credentials.Credentials(**session['credentials'])
            classroom_service = build('classroom', 'v1', credentials=creds)
            
            # Fetch Courses
            courses_result = classroom_service.courses().list(studentId='me', courseStates=['ACTIVE']).execute()
            google_courses = courses_result.get('courses', [])
            
            for course in google_courses:
                classrooms.append({
                    "id": course.get('id'),
                    "name": course.get('name'),
                    "section": course.get('section', ''),
                    "teacher_name": "Teacher" # Hardcoded to prevent frontend charAt(0) crash
                })
                
                # Fetch CourseWork
                courseworks = []
                try:
                    coursework_result = classroom_service.courses().courseWork().list(courseId=course['id']).execute()
                    courseworks = coursework_result.get('courseWork', [])
                except Exception as e:
                    pass
                
                # Fetch Materials (Announcements & CourseWorkMaterials)
                try:
                    announcements_result = classroom_service.courses().announcements().list(courseId=course['id']).execute()
                    for ann in announcements_result.get('announcements', []):
                        materials.append({
                            "id": ann.get('id'),
                            "course_id": course['id'],
                            "course_name": course['name'],
                            "title": ann.get('text', 'Announcement'),
                            "type": "Announcement",
                            "url": ann.get('alternateLink'),
                            "date": ann.get('creationTime')
                        })
                except Exception as e:
                    pass
                    
                try:
                    materials_result = classroom_service.courses().courseWorkMaterials().list(courseId=course['id']).execute()
                    for mat in materials_result.get('courseWorkMaterial', []):
                        materials.append({
                            "id": mat.get('id'),
                            "course_id": course['id'],
                            "course_name": course['name'],
                            "title": mat.get('title', 'Material'),
                            "type": "Material",
                            "url": mat.get('alternateLink'),
                            "date": mat.get('creationTime')
                        })
                except Exception as e:
                    pass
                
                if not courseworks:
                    continue
                    
                # Fetch Submissions
                submissions = []
                try:
                    subs_result = classroom_service.courses().courseWork().studentSubmissions().list(
                        courseId=course['id'],
                        courseWorkId='-' # All coursework
                    ).execute()
                    submissions = subs_result.get('studentSubmissions', [])
                except Exception as e:
                    pass
                
                sub_dict = {sub['courseWorkId']: sub for sub in submissions}
                
                for cw in courseworks:
                    sub = sub_dict.get(cw['id'], {})
                    state = sub.get('state')
                    
                    is_submitted = state in ['TURNED_IN', 'RETURNED']
                    
                    due_date_obj = cw.get('dueDate')
                    due_time_obj = cw.get('dueTime')
                    
                    item = {
                        "id": cw['id'],
                        "course_id": course['id'],
                        "course_name": course['name'],
                        "title": cw['title'],
                        "due_date": f"{due_date_obj['year']}-{due_date_obj['month']:02d}-{due_date_obj['day']:02d}" if due_date_obj else None,
                        "status": state
                    }
                    
                    if is_submitted:
                        assignments["submitted"].append(item)
                    else:
                        if due_date_obj:
                            # Basic check for missing
                            if sub.get('late'):
                                assignments["missing"].append(item)
                            else:
                                assignments["pending"].append(item)
                        else:
                            assignments["pending"].append(item)
                            
        except Exception as e:
            app.logger.exception("Failed to fetch student Google Classroom data")

    # Extract enrolled google course IDs
    enrolled_gc_ids = [c['id'] for c in classrooms]
    
    # Fetch personalized timetable
    timetable_data = []
    if enrolled_gc_ids:
        local_courses = get_courses_by_google_ids(enrolled_gc_ids)
        local_course_ids = [c.get('id') for c in local_courses]
        
        if local_course_ids:
            seen_student_slots = set()
            for local_course in local_courses:
                slots = get_timetable_slots_by_course(local_course.get('id'))
                for slot in slots:
                    # Deduplicate by course_id, day, period (or start_time)
                    signature = f"{local_course.get('id')}_{slot.get('day')}_{slot.get('period', slot.get('start_time'))}"
                    if signature not in seen_student_slots:
                        seen_student_slots.add(signature)
                        timetable_data.append({
                            "id": slot.get('id'),
                            "day": slot.get('day'),
                            "start_time": slot.get('start_time'), # Deprecated fields but keeping for backwards compatibility if needed
                            "end_time": slot.get('end_time'),
                            "period": slot.get('period'),
                            "subject": slot.get('subject'),
                            "google_event_id": slot.get('google_event_id'),
                            "meet_link": local_course.get('meet_link'),
                            "meet_code": local_course.get('meet_code')
                        })

    return jsonify({
        "user": user_info,
        "classrooms": classrooms,
        "assignments": assignments,
        "timetable": timetable_data,
        "materials": sorted(materials, key=lambda x: x['date'] or '', reverse=True)
    })


# ==========================================
# 7. TEACHER TIMETABLE API
# ==========================================



# ==========================================
# 8. STUDENT CALENDAR SYNC
# ==========================================

@app.route('/api/student/calendar/sync', methods=['POST'])
def sync_student_calendar():
    if 'user' not in session or session['user'].get('role') != 'student':
        return jsonify({"error": "Unauthorized"}), 403
        
    if 'credentials' not in session:
        return jsonify({"error": "No Google credentials"}), 401
        
    user_info = session['user']
    
    data = request.json or {}
    slots = data.get('slots', [])
    
    if not slots:
        return jsonify({"message": "No timetable slots provided to sync"}), 400
        
    creds = google.oauth2.credentials.Credentials(**session['credentials'])
    calendar_service = build('calendar', 'v3', credentials=creds)
    
    import datetime as dt
    days_of_week = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
    today = dt.date.today()
                
    synced_count = 0
    for slot in slots:
        try:
            target_day = days_of_week.get(slot.get('day'), 0)
            days_ahead = target_day - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_date = today + dt.timedelta(days_ahead)
            date_str = next_date.isoformat()
            
            def format_time(val):
                if not val: return "00:00"
                if isinstance(val, (int, float)): return f"{int(val):02d}:00"
                s = str(val).strip()
                if ":" in s:
                    p = s.split(':')
                    try: return f"{int(p[0]):02d}:{int(p[1][:2]):02d}"
                    except: pass
                try: return f"{int(s):02d}:00"
                except: return "00:00"
            
            start_t = format_time(slot.get('start_time'))
            end_t = format_time(slot.get('end_time'))

            start_datetime = f"{date_str}T{start_t}:00"
            end_datetime = f"{date_str}T{end_t}:00"
            summary_text = f"{slot.get('subject')} Class"

            # Check for duplicates on the exact same day
            events_result = calendar_service.events().list(
                calendarId='primary', 
                timeMin=f"{date_str}T00:00:00+05:30", 
                timeMax=f"{date_str}T23:59:59+05:30", 
                singleEvents=True,
                q=summary_text
            ).execute()
            
            existing_events = events_result.get('items', [])
            is_duplicate = any(
                e.get('summary') == summary_text for e in existing_events
            )
            
            if is_duplicate:
                app.logger.info(f"Skipping duplicate event: {summary_text} on {date_str}")
                continue

            meet_link = slot.get('meet_link')
            desc = 'ClassOps Auto-synced Student Class'
            if meet_link:
                desc += f'\n\nJoin Class via Meet: {meet_link}'
                
            event = {
                'summary': summary_text,
                'description': desc,
                'start': {
                    'dateTime': start_datetime, 
                    'timeZone': 'Asia/Kolkata',
                },
                'end': {
                    'dateTime': end_datetime,
                    'timeZone': 'Asia/Kolkata',
                },
                'recurrence': ['RRULE:FREQ=WEEKLY'],
            }
            
            if meet_link:
                event['location'] = meet_link
                
            calendar_service.events().insert(calendarId='primary', body=event).execute()
            synced_count += 1
        except Exception as e:
            app.logger.error(f"Failed to sync slot {slot.get('id')}: {e}")
            
    return jsonify({"message": f"Successfully synced {synced_count} classes to your Google Calendar."})

@app.route('/api/student/evaluation', methods=['POST'])
def submit_evaluation():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.json
    course_id = data.get('course_id')
    ratings = data.get('ratings')
    
    if not course_id or not ratings:
        return jsonify({"error": "Missing course_id or ratings"}), 400
        
    student_id = session['user'].get('id')
    if not student_id:
        return jsonify({"error": "Student ID missing from session"}), 400
        
    eval_data = {
        "course_id": course_id,
        "student_id": student_id,
        "student_email": session['user'].get('email'),
        "ratings": ratings,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        from models import put_evaluation
        put_evaluation(course_id, student_id, eval_data)
        return jsonify({"success": True, "message": "Evaluation submitted successfully"})
    except Exception as e:
        app.logger.exception(f"Failed to submit evaluation: {e}")
        return jsonify({"error": "Database error"}), 500

@app.route('/api/courses/<course_id>/evaluations', methods=['GET'])
def get_evaluations(course_id):
    if 'user' not in session or session['user'].get('role') != 'teacher':
        return jsonify({"error": "Unauthorized"}), 403
        
    teacher = get_authenticated_teacher()
    if not teacher:
        return jsonify({"error": "Not authenticated"}), 401
        
    try:
        from models import get_evaluations_by_course
        evaluations = get_evaluations_by_course(course_id)
        
        if not evaluations:
            return jsonify({"evaluations": [], "averages": {}})
            
        # Calculate averages
        averages = {}
        counts = {}
        for ev in evaluations:
            ratings = ev.get('ratings', {})
            for key, val in ratings.items():
                averages[key] = averages.get(key, 0) + val
                counts[key] = counts.get(key, 0) + 1
                
        for key in averages:
            averages[key] = round(averages[key] / counts[key], 2)
            
        return jsonify({
            "evaluations": evaluations,
            "averages": averages
        })
    except Exception as e:
        app.logger.exception(f"Failed to get evaluations: {e}")
        return jsonify({"error": "Database error"}), 500

import csv
import io
from flask import make_response

@app.route('/api/courses/<course_id>/evaluations/download', methods=['GET'])
def download_evaluations(course_id):
    if 'user' not in session or session['user'].get('role') != 'teacher':
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        from models import get_evaluations_by_course
        evaluations = get_evaluations_by_course(course_id)
        
        si = io.StringIO()
        cw = csv.writer(si)
        # 10 Questions
        questions = [
            "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10"
        ]
        headers = ['Student Email', 'Timestamp'] + questions
        cw.writerow(headers)
        
        for ev in evaluations:
            row = [ev.get('student_email', 'Unknown'), ev.get('timestamp', '')]
            ratings = ev.get('ratings', {})
            for q in questions:
                row.append(ratings.get(q, ''))
            cw.writerow(row)
            
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename=course_{course_id}_evaluations.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    except Exception as e:
        app.logger.exception(f"Failed to generate CSV: {e}")
        return jsonify({"error": "Failed to generate CSV"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.logger.info(f"Starting ClassOps backend on port {port}")
    try:
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        app.logger.error(f"Failed to start app: {e}")
        raise