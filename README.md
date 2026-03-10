# ClassOps

ClassOps is a smart teacher automation system.

# 🎓 Teacher Workflow Automation Platform

A **full-stack productivity platform for educators** that automates repetitive academic and administrative tasks such as attendance management, assignment tracking, performance analytics, syllabus progress monitoring, and question paper generation.

This system integrates modern web technologies with educational workflows to help teachers **save time, gain insights about students, and generate reports required for accreditation bodies** like **NBA** and **NAAC**.

---

# 🚀 Features

## 📊 Teacher Dashboard

A centralized dashboard displaying:

* Today's classes
* Attendance alerts
* Weak student identification
* Pending assignments
* Course syllabus progress
* Question paper generator

---

## 🧾 Attendance Management

* Record daily student attendance
* Track attendance history
* Automatically calculate attendance percentage
* Identify students with **low attendance (<75%)**

---

## 📚 Assignment Tracking

* Create assignments for courses
* Track student submissions
* Record assignment marks
* Monitor due dates

---

## 📈 Student Performance Analytics

Automatically calculates:

* Attendance percentage
* Average assignment marks
* At-risk students based on:

  * Attendance < 75%
  * Average marks < 50

---

## 📘 Syllabus Progress Tracking

* Track completion of course modules
* Monitor teaching progress
* Provide syllabus completion data for academic reports

---

## 📝 Question Paper Generator

Automatically generates exam papers using **Bloom’s Taxonomy**:

* **Knowledge** – basic understanding
* **Application** – problem solving
* **Analysis** – conceptual comparison

---

## 🧠 Weak Student Identification

Students are automatically flagged when:

* Attendance percentage is low
* Assignment performance drops

This allows teachers to **intervene early and support students**.

---

# 🏗 System Architecture

```
Frontend (React)
        |
        | REST API
        v
Backend (Flask)
        |
        v
SQLite Database (SQLAlchemy ORM)
```

### Technology Stack

| Layer                   | Technology           |
| ----------------------- | -------------------- |
| Frontend                | ReactJS              |
| API Communication       | Axios                |
| Backend                 | Flask                |
| ORM                     | SQLAlchemy           |
| Database                | SQLite               |
| Authentication (future) | Google OAuth         |
| Integration             | Google Classroom API |

---

# 📁 Project Structure

```
teacher-productivity-system/
│
├── backend/
│   ├── app.py
│   ├── models.py
│   ├── config.py
│   ├── requirements.txt
│   └── database.db
│
├── frontend/
│   ├── package.json
│   ├── public/
│   └── src/
│       ├── App.js
│       ├── api.js
│       │
│       ├── pages/
│       │   ├── Dashboard.js
│       │   ├── Attendance.js
│       │   ├── Students.js
│       │   ├── Assignments.js
│       │   └── QuestionGenerator.js
│       │
│       └── components/
│           ├── Navbar.js
│           ├── StudentTable.js
│           └── AttendanceForm.js
│
└── README.md
```

---

# ⚙️ Installation

## 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/teacher-productivity-system.git
cd teacher-productivity-system
```

---

# 🔧 Backend Setup (Flask)

Navigate to the backend folder:

```bash
cd backend
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the server:

```bash
python app.py
```

Backend will start at:

```
http://localhost:5000
```

---

# 💻 Frontend Setup (React)

Navigate to the frontend folder:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm start
```

Frontend will run at:

```
http://localhost:3000
```

---

# 🗄 Database Design

The system uses **SQLAlchemy ORM with SQLite**.

### Tables

| Table             | Purpose                         |
| ----------------- | ------------------------------- |
| Teacher           | Stores teacher information      |
| Course            | Courses taught by teachers      |
| Student           | Student details and CGPA        |
| Attendance        | Daily attendance records        |
| Assignment        | Assignments created by teachers |
| Submission        | Student assignment submissions  |
| PerformanceMetric | Studen                          |


