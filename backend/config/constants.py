import os
import re

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEET_API_BASE = "https://meet.googleapis.com/v2"
MEETING_CODE_PATTERN = re.compile(r"([a-z]{3}-[a-z]{4}-[a-z]{3})", re.IGNORECASE)

DEFAULT_PERIOD_TIMINGS = [
    {"label": "8-9 AM", "startHour": 8, "endHour": 9},
    {"label": "9-10 AM", "startHour": 9, "endHour": 10},
    {"label": "10-11 AM", "startHour": 10, "endHour": 11},
    {"label": "11-12 PM", "startHour": 11, "endHour": 12},
    {"label": "12-1 PM", "startHour": 12, "endHour": 13},
    {"label": "1-2 PM", "startHour": 13, "endHour": 14},
    {"label": "2-3 PM", "startHour": 14, "endHour": 15},
    {"label": "3-4 PM", "startHour": 15, "endHour": 16},
]

CLIENT_SECRETS_FILE = os.getenv(
    "CLIENT_SECRETS_FILE",
    os.path.join(BACKEND_DIR, "client_secret.json"),
)

SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
    "https://www.googleapis.com/auth/classroom.profile.emails",
    "https://www.googleapis.com/auth/classroom.student-submissions.students.readonly",
    "https://www.googleapis.com/auth/classroom.student-submissions.me.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students",
    "https://www.googleapis.com/auth/classroom.coursework.students.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
    "https://www.googleapis.com/auth/classroom.announcements.readonly",
    "https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly",
    "https://www.googleapis.com/auth/meetings.space.readonly",
    "https://www.googleapis.com/auth/calendar",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.file",
]

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

DEFAULT_CORS_ORIGINS = [
    "https://classops-6.onrender.com",
    "http://localhost:5173",
    "http://localhost:5000",
]


def _split_env_list(value):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


ALLOWED_CORS_ORIGINS = list(
    dict.fromkeys(
        DEFAULT_CORS_ORIGINS
        + _split_env_list(os.getenv("CORS_ORIGINS"))
        + _split_env_list(os.getenv("FRONTEND_URL"))
        + _split_env_list(os.getenv("BASE_URL"))
    )
)

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
