from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    courses = db.relationship('Course', backref='teacher', lazy=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_course_id = db.Column(db.String(120), unique=True, nullable=True)
    name = db.Column(db.String(200), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    students = db.relationship('Student', backref='course', lazy=True)
    targets = db.relationship('MaterialTarget', backref='course', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    attendances = db.relationship('Attendance', backref='student', lazy=True)
    metrics = db.relationship('StudentMetric', backref='student', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
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