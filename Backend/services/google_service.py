import google.oauth2.credentials
from flask import current_app, request, session
from google.auth.transport.requests import AuthorizedSession
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build

from config.constants import MEET_API_BASE
from repositories import dynamodb_repository as db
from services.teacher_service import get_owned_course_or_404
from utils.meet_helpers import (
    build_attendance_row,
    build_meet_link,
    format_google_timestamp,
    normalize_email,
    normalize_meeting_code,
)


def build_credentials_payload(credentials):
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }


def ensure_google_credentials(credentials_dict=None, persist_session=True):
    if credentials_dict is None:
        credentials_dict = session.get("credentials")
        persist_session = True
    if not credentials_dict:
        return None

    creds = google.oauth2.credentials.Credentials(**credentials_dict)
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleAuthRequest())
        if persist_session:
            session["credentials"] = build_credentials_payload(creds)
            session.modified = True
    return creds


def get_missing_scopes(*required_scopes):
    granted = set((session.get("credentials") or {}).get("scopes") or [])
    return [scope for scope in required_scopes if scope not in granted]


def get_redirect_uri():
    import os

    explicit_redirect_uri = os.getenv("REDIRECT_URI")
    if explicit_redirect_uri:
        return explicit_redirect_uri

    base = os.getenv("BASE_URL", request.host_url.rstrip("/"))
    if "onrender.com" in base:
        base = base.replace("http://", "https://")
    elif "127.0.0.1" in base:
        base = base.replace("127.0.0.1", "localhost")
        
    return f"{base}/api/auth/google/callback"


def get_classroom_service(credentials_dict=None):
    creds = ensure_google_credentials(credentials_dict)
    if not creds:
        return None

    current_app.logger.info("Current Token Scopes: %s", getattr(creds, "scopes", None))
    return build("classroom", "v1", credentials=creds)


def get_drive_service(credentials_dict=None):
    creds = ensure_google_credentials(credentials_dict)
    if not creds:
        return None
    return build("drive", "v3", credentials=creds)


def list_meet_collection(resource_path, item_key, creds, params=None):
    authorized_session = AuthorizedSession(creds)
    collection = []
    page_token = None
    while True:
        query_params = dict(params or {})
        if page_token:
            query_params["pageToken"] = page_token

        response = authorized_session.get(
            f"{MEET_API_BASE}/{resource_path.lstrip('/')}",
            params=query_params,
            timeout=30,
        )
        if not response.ok:
            if response.status_code in (401, 403):
                raise ValueError("Google Meet access expired. Please reconnect your Google account and try again.")
            raise ValueError(f"Meet API error ({response.status_code}): {response.text}")

        payload = response.json()
        collection.extend(payload.get(item_key, []))
        page_token = payload.get("nextPageToken")
        if not page_token:
            break
    return collection


def extract_meet_user_id(participant):
    signed_in_user = participant.get("signedinUser") or {}
    user_name = signed_in_user.get("user") or ""
    return user_name.split("/")[-1] if user_name else None


def resolve_classroom_email(classroom_service, user_id, cache):
    if not classroom_service or not user_id:
        return None
    if user_id in cache:
        return cache[user_id]

    try:
        profile = classroom_service.userProfiles().get(userId=user_id).execute()
        email = normalize_email(profile.get("emailAddress"))
    except Exception as exc:
        current_app.logger.warning("Could not resolve Classroom email for %s: %s", user_id, exc)
        email = None

    cache[user_id] = email
    return email


def get_meeting_link(course_id, credentials_dict=None):
    course = get_owned_course_or_404(course_id)
    classroom_service = get_classroom_service(credentials_dict)
    classroom_course = {}

    if course.get("google_course_id") and classroom_service:
        classroom_course = classroom_service.courses().get(id=course.get("google_course_id")).execute()

    api_meet_link = classroom_course.get("meetLink") or classroom_course.get("meetingLink")
    stored_meet_link = (course.get("meet_link") or "").strip() or None
    meeting_code = (
        normalize_meeting_code(api_meet_link)
        or normalize_meeting_code(course.get("meet_code"))
        or normalize_meeting_code(stored_meet_link)
    )
    meet_link = api_meet_link or stored_meet_link or build_meet_link(meeting_code)

    source = "classroom_api" if api_meet_link else ("stored_config" if stored_meet_link or meeting_code else "unavailable")
    warning = None
    if not api_meet_link:
        warning = (
            "Google Classroom's documented Course resource does not expose a meetLink field. "
            "ClassOps uses the saved Meet link/code when Classroom does not return one."
        )

    return {
        "courseId": course.get("id") or course.get("google_course_id"),
        "courseName": course.get("name"),
        "googleCourseId": course.get("google_course_id"),
        "meetLink": meet_link,
        "meetingCode": meeting_code,
        "source": source,
        "classroomAlternateLink": classroom_course.get("alternateLink"),
        "warning": warning,
    }


def get_attendance_report(meeting_code, course_id=None, credentials_dict=None):
    normalized_code = normalize_meeting_code(meeting_code)
    if not normalized_code:
        raise ValueError("A valid Google Meet code is required.")

    creds = ensure_google_credentials(credentials_dict)
    if not creds:
        raise ValueError("Missing Google credentials. Please authenticate again.")

    conference_records = list_meet_collection(
        "conferenceRecords",
        "conferenceRecords",
        creds,
        params={
            "filter": f'space.meeting_code = "{normalized_code}"',
            "pageSize": 1,
        },
    )

    if not conference_records:
        return {
            "meetingCode": normalized_code,
            "conferenceRecord": None,
            "conferenceStartTime": None,
            "conferenceEndTime": None,
            "meetingEnded": False,
            "attendance": [],
            "unmatchedParticipants": [],
            "presentStudentIds": [],
            "status": "waiting_for_record",
        }

    conference_record = conference_records[0]
    participants = list_meet_collection(
        f"{conference_record['name']}/participants",
        "participants",
        creds,
        params={"pageSize": 100},
    )

    classroom_service = get_classroom_service(credentials_dict) if course_id else None
    email_cache = {}
    attendance = []
    unmatched_participants = []
    present_student_ids = []
    meeting_ended = bool(conference_record.get("endTime"))
    live_present_count = 0
    excluded_emails = {
        normalize_email(session.get("user", {}).get("email")),
    }
    excluded_emails = {email for email in excluded_emails if email}

    student_by_email = {}
    if course_id:
        for student in db.get_students_by_course(course_id):
            if student.get("email"):
                student_by_email[normalize_email(student.get("email"))] = student

    for participant in participants:
        join_time = participant.get("earliestStartTime")
        leave_time = participant.get("latestEndTime")
        user_id = extract_meet_user_id(participant)
        email = resolve_classroom_email(classroom_service, user_id, email_cache)

        if email in excluded_emails:
            continue

        if email:
            from email_parser import parse_jerusalem_email

            parsed = parse_jerusalem_email(email)
            if parsed["role"] == "teacher":
                continue

        matched_student = student_by_email.get(email) if email else None
        participant_sessions = list_meet_collection(
            f"{participant['name']}/participantSessions",
            "participantSessions",
            creds,
            params={"pageSize": 100},
        )

        if participant_sessions:
            join_candidates = [item.get("startTime") for item in participant_sessions if item.get("startTime")]
            if join_time:
                join_candidates.append(join_time)
            join_time = min(join_candidates) if join_candidates else join_time

            leave_candidates = [item.get("endTime") for item in participant_sessions if item.get("endTime")]
            leave_time = max(leave_candidates) if leave_candidates else None

        if not leave_time:
            meeting_ended = False
            live_present_count += 1

        row = build_attendance_row(
            matched_student.get("name") if matched_student else f"Participant {participant.get('name', '').split('/')[-1]}",
            email,
            join_time,
            leave_time,
            sessions=participant_sessions,
            student=matched_student,
        )

        if matched_student:
            attendance.append(row)
            present_student_ids.append(matched_student.get("id", matched_student.get("roll_number")))
        else:
            unmatched_participants.append(row)

    attendance = sort_participant_rows(attendance)
    unmatched_participants = sort_participant_rows(unmatched_participants)
    all_participants = sort_participant_rows(attendance + unmatched_participants)

    return {
        "meetingCode": normalized_code,
        "conferenceRecord": conference_record.get("name"),
        "conferenceStartTime": format_google_timestamp(conference_record.get("startTime")),
        "conferenceEndTime": format_google_timestamp(conference_record.get("endTime")),
        "meetingEnded": meeting_ended,
        "livePresentCount": live_present_count,
        "participantCount": len(all_participants),
        "attendance": attendance,
        "unmatchedParticipants": unmatched_participants,
        "allParticipants": all_participants,
        "presentStudentIds": present_student_ids,
        "status": "completed" if meeting_ended else "in_progress",
    }


def build_meet_export_rows(report):
    rows = []
    for row in report.get("allParticipants") or report.get("attendance") or []:
        rows.append(
            {
                "studentName": row.get("studentName"),
                "rollNumber": row.get("rollNumber"),
                "email": row.get("email"),
                "joinTime": row.get("joinTime"),
                "leaveTime": row.get("leaveTime"),
                "totalDurationMinutes": row.get("totalDurationMinutes"),
                "sessionCount": row.get("sessionCount"),
                "rejoinCount": row.get("rejoinCount"),
                "activeNow": row.get("activeNow"),
            }
        )
    return rows


def sort_participant_rows(rows):
    return sorted(
        rows or [],
        key=lambda item: (
            (item.get("studentName") or "").strip().lower(),
            (item.get("email") or "").strip().lower(),
        ),
    )


def sync_classroom_data(credentials_dict=None):
    service = get_classroom_service(credentials_dict)
    if not service:
        raise ValueError("Missing Google credentials. Please authenticate first.")

    user_info = session.get("user")
    if not user_info:
        raise ValueError("User info not found in session.")

    email = user_info.get("email")

    # Fetch courses from Google Classroom
    results = service.courses().list(pageSize=10).execute()
    courses_data = results.get("courses", [])

    for course_item in courses_data:
        course_id = course_item["id"]
        existing = db.get_course(email, course_id)
        if not existing:
            new_course = {
                "id": course_id,
                "google_course_id": course_id,
                "name": course_item["name"],
                "teacher_id": email,
                "hours_per_week": 3,
                "meet_link": None,
                "meet_code": None,
            }
            db.put_course(email, new_course)
        else:
            # Update teacher association if needed
            if existing.get("teacher_id") != email:
                existing["teacher_id"] = email
                db.put_course(email, existing)

    return courses_data
