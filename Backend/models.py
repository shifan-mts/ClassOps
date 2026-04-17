from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    availability = db.Column(db.JSON, nullable=True) # Store {Day: [slots]}
    period_timings = db.Column(db.JSON, nullable=True)
    courses = db.relationship('Course', backref='teacher', lazy=True)
    timetable = db.relationship('Timetable', backref='teacher', uselist=False, lazy=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_course_id = db.Column(db.String(120), unique=True, nullable=True)
    name = db.Column(db.String(200), nullable=False)
    hours_per_week = db.Column(db.Integer, default=3)
    meet_link = db.Column(db.String(255), nullable=True)
    meet_code = db.Column(db.String(32), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    students = db.relationship('Student', backref='course', lazy=True)
    targets = db.relationship('MaterialTarget', backref='course', lazy=True)
    assignments = db.relationship('Assignment', backref='course', lazy=True)

class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    slots = db.relationship('TimetableSlot', backref='timetable', cascade="all, delete-orphan", lazy=True)

class TimetableSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timetable_id = db.Column(db.Integer, db.ForeignKey('timetable.id'), nullable=False)
    day = db.Column(db.String(20), nullable=False) # Monday, etc.
    period = db.Column(db.Integer, nullable=True) # Optional for UI index
    start_time = db.Column(db.String(10), nullable=True) # e.g., 10:00
    end_time = db.Column(db.String(10), nullable=True)   # e.g., 11:00
    dept = db.Column(db.String(50), nullable=True)       # e.g., CSE
    year = db.Column(db.Integer, nullable=True)          # e.g., 3
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    subject = db.Column(db.String(120), nullable=False)
    google_event_id = db.Column(db.String(255), nullable=True)
    course = db.relationship('Course')

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_assignment_id = db.Column(db.String(120), unique=True, nullable=True) # Now optional
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    submissions = db.relationship('StudentSubmission', backref='assignment', lazy=True)

class StudentSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    status = db.Column(db.String(50), default='pending') # pending, submitted, missing, graded
    submitted_at = db.Column(db.DateTime, nullable=True)
    score = db.Column(db.Float, nullable=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    dept = db.Column(db.String(50), nullable=True)
    batch = db.Column(db.Integer, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    attendances = db.relationship('Attendance', backref='student', lazy=True)
    metrics = db.relationship('StudentMetric', backref='student', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), nullable=False) # 'Present', 'Absent'
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

class MaterialTarget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(200), nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

class StudentMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_name = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Float, nullable=False)
    plagiarism_score = db.Column(db.Float, nullable=True)
    ai_usage_score = db.Column(db.Float, nullable=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)


