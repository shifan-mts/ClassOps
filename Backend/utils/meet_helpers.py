from config.constants import MEETING_CODE_PATTERN
from datetime import datetime, timezone

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

def sort_participant_rows(rows):
    return sorted(rows, key=lambda x: x.get('studentName') or '')
