import os
import requests
from flask import Flask, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from flask_session import Session
from models import db, Teacher, Course, Student, Attendance, MaterialTarget, StudentMetric
from dotenv import load_dotenv
import google.oauth2.credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import openai
from datetime import datetime
from ai_checker import handle_upload, analyze_text

load_dotenv()
if os.getenv("FLASK_ENV") != "production":
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super_secret_dev_key')
CORS(app, supports_credentials=True)

# SQLite Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///teacher_os.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Server-side sessions to avoid oversized cookie payloads for OAuth tokens
session_dir = os.path.join(app.instance_path, "sessions")
os.makedirs(session_dir, exist_ok=True)
app.config.update(
    SESSION_TYPE="filesystem",
    SESSION_FILE_DIR=session_dir,
    SESSION_PERMANENT=False,
    SESSION_USE_SIGNER=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False
)
Session(app)
db.init_app(app)

# ==========================================
# API KEYS (To be filled in .env file)
# ==========================================
OPENAI_API_KEY = os.getenv('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')
CLIENT_SECRETS_FILE = "client_secret.json" # Download from Google Cloud Console
SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly', 
          'https://www.googleapis.com/auth/classroom.rosters.readonly']

# Initialize DB
with app.app_context():
    db.create_all()

def sync_classroom_data(credentials_dict):
    creds = google.oauth2.credentials.Credentials(**credentials_dict)
    service = build('classroom', 'v1', credentials=creds)

    results = service.courses().list(pageSize=10).execute()
    courses = results.get('courses', [])

    for c in courses:
        if not Course.query.filter_by(google_course_id=c['id']).first():
            new_course = Course(google_course_id=c['id'], name=c['name'], teacher_id=1) # Assuming Teacher 1
            db.session.add(new_course)
    db.session.commit()
    return courses

# ==========================================
# 1. GOOGLE CLASSROOM INTEGRATION
# ==========================================
@app.route('/api/auth/google')
def google_auth():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES
    )
    flow.redirect_uri = url_for('google_auth_callback', _external=True)
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
    flow.redirect_uri = url_for('google_auth_callback', _external=True)
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
    flow.redirect_uri = url_for('google_auth_callback', _external=True)
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
    return redirect('http://localhost:5173/dashboard') # Redirect to React App

@app.route('/api/classroom/sync')
def sync_classroom():
    if 'credentials' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    courses = sync_classroom_data(session['credentials'])
    return jsonify({"message": "Classroom synced successfully", "courses": courses})

# ==========================================
# 2. AI CONTENT DETECTION (RapidAPI)
# ==========================================
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

# ==========================================
# 3. QUESTION PAPER CREATION (BLOOM'S TAXONOMY)
# ==========================================
@app.route('/api/question-paper/generate', methods=['POST'])
def generate_question_paper():
    data = request.json
    topic = data.get('topic')
    difficulty = data.get('difficulty', 'Medium')
    
    openai.api_key = OPENAI_API_KEY
    prompt = f"""Generate a university-level question paper on '{topic}' with a '{difficulty}' difficulty. 
    Format it strictly according to Bloom's Taxonomy:
    Part A (Remember & Understand) - 5 short questions
    Part B (Apply & Analyze) - 3 medium questions
    Part C (Evaluate & Create) - 2 essay questions"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a university professor."},
                  {"role": "user", "content": prompt}]
    )
    
    return jsonify({"question_paper": response.choices[0].message.content})

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
@app.route('/api/attendance', methods=['POST'])
def mark_attendance():
    data = request.json
    for record in data['records']: # List of {student_id, status}
        att = Attendance(student_id=record['student_id'], status=record['status'])
        db.session.add(att)
    db.session.commit()
    return jsonify({"message": "Attendance recorded"}), 200

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




