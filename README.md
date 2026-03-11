# ClassOps: Smart Teacher Workflow Automation

ClassOps is a productivity ecosystem designed to liberate teachers from the "administrative tax" that leads to burnout. By automating daily administrative chores, it allows educators to focus on what matters most: teaching and mentoring students.

## The Problem (Stakeholder Pain Points)

Modern teaching has become an administrative nightmare. We identified three core stakeholders and the friction points they face:

1.  **The Overburdened Teacher:**
    *   **Pain Point:** Spending hours manually reconciling Assignment submissions with attendance logs and syllabus targets.
    *   **Pain Point:** The "Grading Fatigue" caused by repetitively checking for plagiarism and AI-generated content in student submissions.
    *   *How ClassOps Helps:* Automates the boring stuff. One-click sync for students and assignments, automated timetable generation, and batch AI/Plagiarism analysis.

2.  **The Institution Head/Principal:**
    *   **Pain Point:** Lack of real-time visibility into whether the syllabus is actually being covered (Material Target Completion).
    *   **Pain Point:** Difficulty in maintaining fair and optimized schedules for staff.
    *   *How ClassOps Helps:* Provides a dashboard for tracking material completion and uses a backtracking scheduler to create optimized, collision-free timetables.

3.  **The Student:**
    *   **Pain Point:** Delayed feedback on assignments and inconsistent course structure.
    *   *How ClassOps Helps:* Faster grading turnaround and a consistent structure that maps questions to specific Course Outcomes (CO).

## Key Features

*   **Google Classroom Integration:** Seamlessly sync courses, students, and assignments. No more manual data entry.
*   **Backtracking Timetable Scheduler:** Handles teacher availability and course loads to generate an optimized weekly schedule.
*   **AI Grade-Shield:** Batch analyze student submissions for AI-generated content and plagiarism.
*   **Bloom’s Taxonomy Question Generator:** Create high-quality question papers mapped to Course Outcomes (CO) using GPT-3.5.
*   **Attendance & Material Tracking:** Monitor student presence and syllabus progress in one place.

## Tech Stack

*   **Frontend:** React (Vite), Tailwind CSS, Lucide Icons.
*   **Backend:** Flask (Python), SQLAlchemy (SQLite).
*   **Intelligence:** OpenAI API (GPT-3.5), Custom AI Analysis Logic.
*   **Integrations:** Google Classroom API, Google OAuth 2.0.

## Getting Started

### Backend Setup

1.  Navigate to `/Backend`.
2.  Install dependencies: `pip install -r requirements.txt`.
3.  Configure your `.env` file:
    ```env
    FLASK_SECRET_KEY=your_secret_key
    OPENAI_API_KEY=your_openai_key
    ```
4.  Download your `client_secret.json` from Google Cloud Console and place it in the `Backend` folder.
5.  Run the server: `python app.py`.

### Frontend Setup

1.  Navigate to `/Frontend`.
2.  Install dependencies: `npm install`.
3.  Run the development server: `npm run dev`.

---
*Built for educators who deserve better tools.*
