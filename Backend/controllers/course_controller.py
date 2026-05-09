from flask import current_app, jsonify, request, session

from repositories import dynamodb_repository as db
from services.google_service import get_classroom_service, get_meeting_link
from services.teacher_service import get_authenticated_teacher, get_owned_course_or_404
from utils.meet_helpers import build_meet_link, normalize_email, normalize_meeting_code


def get_courses():
    if "user" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    teacher = get_authenticated_teacher()
    courses = db.get_courses_by_teacher(teacher["email"]) if teacher else []
    return jsonify(
        [
            {
                "id": course.get("id"),
                "google_course_id": course.get("google_course_id"),
                "name": course.get("name"),
                "hours_per_week": course.get("hours_per_week", 3),
                "meet_link": course.get("meet_link"),
                "meeting_code": course.get("meet_code"),
            }
            for course in courses
        ]
    )


def course_meeting_config(course_id):
    if "user" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    course = get_owned_course_or_404(course_id)
    if not course:
        return jsonify({"error": "Forbidden"}), 403

    if request.method == "POST":
        data = request.json or {}
        meeting_code = normalize_meeting_code(data.get("meeting_code") or data.get("meet_link"))
        meet_link = (data.get("meet_link") or "").strip() or build_meet_link(meeting_code)

        if not meeting_code and not meet_link:
            return jsonify({"error": "Provide a Meet link or meeting code."}), 400

        course["meet_code"] = meeting_code
        course["meet_link"] = meet_link
        email = session.get("user", {}).get("email")
        db.put_course(email, course)

    try:
        return jsonify(get_meeting_link(course_id)), 200
    except Exception as exc:
        current_app.logger.exception("Failed to resolve meeting config: %s", exc)
        return jsonify({"error": str(exc)}), 500


def sync_students_for_course(course_id):
    service = get_classroom_service()
    if not service:
        return jsonify({"error": "Not authenticated"}), 401

    course = get_owned_course_or_404(course_id)
    if not course:
        return jsonify({"error": "Forbidden"}), 403
    if not course.get("google_course_id"):
        return jsonify({"error": "Course not linked to Google Classroom"}), 400

    try:
        students_data = []
        next_page_token = None
        while True:
            results = (
                service.courses()
                .students()
                .list(courseId=course.get("google_course_id"), pageToken=next_page_token)
                .execute()
            )
            students_data.extend(results.get("students", []))
            next_page_token = results.get("nextPageToken")
            if not next_page_token:
                break

        existing_students = db.get_students_by_course(course_id)
        existing_rolls = {student.get("roll_number"): student for student in existing_students}

        count = 0
        for student_data in students_data:
            student_id_google = student_data.get("userId")
            if not student_id_google:
                continue

            profile = student_data.get("profile", {})
            name = profile.get("name", {}).get("fullName", "Unknown Student")
            email = normalize_email(profile.get("emailAddress"))

            existing = existing_rolls.get(student_id_google)
            if not existing:
                new_student = {
                    "id": student_id_google,
                    "roll_number": student_id_google,
                    "name": name,
                    "email": email,
                    "course_id": course_id,
                }
                db.sync_student(course_id, new_student)
                count += 1
            else:
                existing["name"] = name
                existing["email"] = email or existing.get("email")
                db.sync_student(course_id, existing)

        return jsonify({"message": f"Synced {count} new students successfully"}), 200
    except Exception as exc:
        current_app.logger.exception("Student sync failed: %s", exc)
        return jsonify({"error": f"Classroom API error: {str(exc)}"}), 500


def get_students(course_id):
    students = db.get_students_by_course(course_id)
    return (
        jsonify(
            [
                {
                    "id": student.get("id", student.get("roll_number")),
                    "name": student.get("name"),
                    "roll_number": student.get("roll_number"),
                    "email": student.get("email"),
                }
                for student in students
            ]
        ),
        200,
    )
