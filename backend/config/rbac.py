INITIAL_COMPONENTS = [
    {
        "id": "teacher-dashboard", 
        "name": "Institutional Insights", 
        "description": "The primary control center for staff. Provides a birds-eye view of institutional metrics, overall syllabus completion status, and global academic stats."
    },
    {
        "id": "student-dashboard", 
        "name": "Student Portal", 
        "description": "The personalized hub for students. Includes the assignment tracker, classroom materials viewer, and a direct link to submit course evaluations."
    },
    {
        "id": "attendance", 
        "name": "Attendance Management", 
        "description": "A robust tool for subject-wise tracking. Supports Google Classroom roster synchronization and exporting high-fidelity CSV reports for compliance."
    },
    {
        "id": "meet", 
        "name": "Class Meetings", 
        "description": "A specialized panel to manage Google Meet links and track student participation during live online sessions."
    },
    {
        "id": "ai-tools", 
        "name": "AI Assistant & Analytics", 
        "description": "AI-powered suite for generating Bloom's Taxonomy question papers and performing cross-submission plagiarism analysis using Gemini."
    },
    {
        "id": "evaluation", 
        "name": "Student Evaluations", 
        "description": "The grading and feedback engine. Allows teachers to provide detailed feedback and students to submit anonymous course reviews."
    },
    {
        "id": "timetable", 
        "name": "Class Timetable", 
        "description": "Institutional scheduling system. Maps subjects to periods and syncs classroom timings directly to user Google Calendars."
    }
]

INITIAL_ROLES = {
    "teacher": {
        "teacher-dashboard": ["view", "edit"],
        "student-dashboard": [],
        "attendance": ["view", "edit"],
        "meet": ["view", "edit"],
        "ai-tools": ["view", "edit"],
        "evaluation": ["view", "edit"],
        "timetable": ["view", "edit"],
        "department": "Common"
    },
    "student": {
        "teacher-dashboard": [],
        "student-dashboard": ["view"],
        "attendance": [],
        "meet": [],
        "ai-tools": [],
        "evaluation": ["view"],
        "timetable": ["view"],
        "department": "Common"
    },
    "visitor": {
        "teacher-dashboard": ["view"],
        "student-dashboard": [],
        "attendance": [],
        "meet": [],
        "ai-tools": [],
        "evaluation": [],
        "timetable": [],
        "department": "Common"
    }
}
