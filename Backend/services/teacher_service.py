from flask import abort, session

from config.constants import DEFAULT_PERIOD_TIMINGS
from repositories import dynamodb_repository as db


def get_default_period_timings():
    return [dict(item) for item in DEFAULT_PERIOD_TIMINGS]


def normalize_period_timings(period_timings):
    cleaned = []
    for index, default_period in enumerate(DEFAULT_PERIOD_TIMINGS):
        current = period_timings or []
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
        cleaned.append(
            {
                "label": label,
                "startHour": start_hour,
                "endHour": end_hour,
            }
        )
    return cleaned


def get_authenticated_teacher():
    email = session.get("user", {}).get("email")
    return db.get_teacher(email) if email else None


def get_owned_course_or_404(course_id):
    teacher = get_authenticated_teacher()
    if not teacher:
        abort(401)

    course = db.get_course(teacher["email"], str(course_id))
    if not course:
        abort(404)

    return course
