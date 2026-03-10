import os
import requests
from flask import Flask, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from models import db, Teacher, Course, Student, Attendance, MaterialTarget, StudentMetric
from dotenv import load_dotenv
import google.oauth2.credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import openai
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super_secret_dev_key')
CORS(app, supports_credentials=True)

# SQLite Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///teacher_os.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# ==========================================
# API KEYS (To be filled in .env file)
# ==========================================
GPTZERO_API_KEY = os.getenv('GPTZERO_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CLIENT_SECRETS_FILE = "client_secret.json" # Download from Google Cloud Console
SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly', 
          'https://www.googleapis.com/auth/classroom.rosters.readonly']

# Initialize DB
with app.app_context():
    db.create_all()

# ==========================================
# 1. GOOGLE CLASSROOM INTEGRATION
# ==========================================
@app.route('/api/auth/google')
def google_auth():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES,
        redirect_uri=url_for('google_auth_callback', _external=True)
    )
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    return jsonify({"auth_url": authorization_url})

@app.route('/api/auth/google/callback')
def google_auth_callback():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES,
        redirect_uri=url_for('google_auth_callback', _external=True)
    )
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    return redirect('http://localhost:5173/dashboard') # Redirect to React App

@app.route('/api/classroom/sync')
def sync_classroom():
    if 'credentials' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    creds = google.oauth2.credentials.Credentials(**session['credentials'])
    service = build('classroom', 'v1', credentials=creds)
    
    # Fetch Courses
    results = service.courses().list(pageSize=10).execute()
    courses = results.get('courses', [])
    
    # Save to DB logic here (simplified for brevity)
    for c in courses:
        if not Course.query.filter_by(google_course_id=c['id']).first():
            new_course = Course(google_course_id=c['id'], name=c['name'], teacher_id=1) # Assuming Teacher 1
            db.session.add(new_course)
    db.session.commit()
    return jsonify({"message": "Classroom synced successfully", "courses": courses})

# ==========================================
# 2. AI PLAGIARISM & USAGE (GPTZERO)
# ==========================================
@app.route('/api/assignments/check', methods=['POST'])
def check_plagiarism():
    data = request.json
    text_to_check = data.get('text')
    
    headers = {
        'Accept': 'application/json',
        'x-api-key': GPTZERO_API_KEY,
        'Content-Type': 'application/json'
    }
    payload = {"document": text_to_check}
    
    # GPTZero API Call
    response = requests.post('https://api.gptzero.me/v2/predict/text', headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        ai_score = result['documents'][0]['completely_generated_prob']
        return jsonify({"ai_probability": ai_score})
    return jsonify({"error": "Failed to check"}), 500

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