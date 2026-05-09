import csv
import datetime as dt
import io
from datetime import datetime, timezone

import google.oauth2.credentials
from flask import current_app, jsonify, make_response, request, session
from googleapiclient.discovery import build

from repositories import dynamodb_repository as db
from services.teacher_service import get_authenticated_teacher


def student_dashboard():
    if "user" not in session or session["user"].get("role") != "student":
        return jsonify({"error": "Unauthorized. Student access required."}), 403

    user_info = session["user"]

    classrooms = []
    assignments = {
        "pending": [],
        "submitted": [],
        "missing": [],
    }
    materials = []

    if "credentials" in session:
        try:
            creds = google.oauth2.credentials.Credentials(**session["credentials"])
            classroom_service = build("classroom", "v1", credentials=creds)

            courses_result = classroom_service.courses().list(studentId="me", courseStates=["ACTIVE"]).execute()
            google_courses = courses_result.get("courses", [])

            for course in google_courses:
                classrooms.append(
                    {
                        "id": course.get("id"),
                        "name": course.get("name"),
                        "section": course.get("section", ""),
                        "teacher_name": "Teacher",
                    }
                )

                courseworks = []
                try:
                    coursework_result = classroom_service.courses().courseWork().list(courseId=course["id"]).execute()
                    courseworks = coursework_result.get("courseWork", [])
                except Exception:
                    pass

                try:
                    announcements_result = classroom_service.courses().announcements().list(courseId=course["id"]).execute()
                    for announcement in announcements_result.get("announcements", []):
                        materials.append(
                            {
                                "id": announcement.get("id"),
                                "course_id": course["id"],
                                "course_name": course["name"],
                                "title": announcement.get("text", "Announcement"),
                                "type": "Announcement",
                                "url": announcement.get("alternateLink"),
                                "date": announcement.get("creationTime"),
                            }
                        )
                except Exception:
                    pass

                try:
                    materials_result = (
                        classroom_service.courses().courseWorkMaterials().list(courseId=course["id"]).execute()
                    )
                    for material in materials_result.get("courseWorkMaterial", []):
                        materials.append(
                            {
                                "id": material.get("id"),
                                "course_id": course["id"],
                                "course_name": course["name"],
                                "title": material.get("title", "Material"),
                                "type": "Material",
                                "url": material.get("alternateLink"),
                                "date": material.get("creationTime"),
                            }
                        )
                except Exception:
                    pass

                if not courseworks:
                    continue

                submissions = []
                try:
                    subs_result = (
                        classroom_service.courses()
                        .courseWork()
                        .studentSubmissions()
                        .list(courseId=course["id"], courseWorkId="-")
                        .execute()
                    )
                    submissions = subs_result.get("studentSubmissions", [])
                except Exception:
                    pass

                sub_dict = {submission["courseWorkId"]: submission for submission in submissions}

                for coursework in courseworks:
                    submission = sub_dict.get(coursework["id"], {})
                    state = submission.get("state")

                    is_submitted = state in ["TURNED_IN", "RETURNED"]

                    due_date_obj = coursework.get("dueDate")

                    item = {
                        "id": coursework["id"],
                        "course_id": course["id"],
                        "course_name": course["name"],
                        "title": coursework["title"],
                        "due_date": (
                            f"{due_date_obj['year']}-{due_date_obj['month']:02d}-{due_date_obj['day']:02d}"
                            if due_date_obj
                            else None
                        ),
                        "status": state,
                    }

                    if is_submitted:
                        assignments["submitted"].append(item)
                    else:
                        if due_date_obj:
                            if submission.get("late"):
                                assignments["missing"].append(item)
                            else:
                                assignments["pending"].append(item)
                        else:
                            assignments["pending"].append(item)

        except Exception:
            current_app.logger.exception("Failed to fetch student Google Classroom data")

    enrolled_gc_ids = [course["id"] for course in classrooms]

    timetable_data = []
    if enrolled_gc_ids:
        local_courses = db.get_courses_by_google_ids(enrolled_gc_ids)
        local_course_ids = [course.get("id") for course in local_courses]

        if local_course_ids:
            seen_student_slots = set()
            for local_course in local_courses:
                slots = db.get_timetable_slots_by_course(local_course.get("id"))
                for slot in slots:
                    signature = f"{local_course.get('id')}_{slot.get('day')}_{slot.get('period', slot.get('start_time'))}"
                    if signature not in seen_student_slots:
                        seen_student_slots.add(signature)
                        timetable_data.append(
                            {
                                "id": slot.get("id"),
                                "day": slot.get("day"),
                                "start_time": slot.get("start_time"),
                                "end_time": slot.get("end_time"),
                                "period": slot.get("period"),
                                "subject": slot.get("subject"),
                                "google_event_id": slot.get("google_event_id"),
                                "meet_link": local_course.get("meet_link"),
                                "meet_code": local_course.get("meet_code"),
                            }
                        )

    return jsonify(
        {
            "user": user_info,
            "classrooms": classrooms,
            "assignments": assignments,
            "timetable": timetable_data,
            "materials": sorted(materials, key=lambda item: item["date"] or "", reverse=True),
        }
    )


def sync_student_calendar():
    if "user" not in session or session["user"].get("role") != "student":
        return jsonify({"error": "Unauthorized"}), 403

    if "credentials" not in session:
        return jsonify({"error": "No Google credentials"}), 401

    data = request.json or {}
    slots = data.get("slots", [])

    if not slots:
        return jsonify({"message": "No timetable slots provided to sync"}), 400

    creds = google.oauth2.credentials.Credentials(**session["credentials"])
    calendar_service = build("calendar", "v3", credentials=creds)

    days_of_week = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
    today = dt.date.today()

    synced_count = 0
    for slot in slots:
        try:
            target_day = days_of_week.get(slot.get("day"), 0)
            days_ahead = target_day - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_date = today + dt.timedelta(days_ahead)
            date_str = next_date.isoformat()

            def format_time(value):
                if not value:
                    return "00:00"
                if isinstance(value, (int, float)):
                    return f"{int(value):02d}:00"
                text_value = str(value).strip()
                if ":" in text_value:
                    parts = text_value.split(":")
                    try:
                        return f"{int(parts[0]):02d}:{int(parts[1][:2]):02d}"
                    except Exception:
                        pass
                try:
                    return f"{int(text_value):02d}:00"
                except Exception:
                    return "00:00"

            start_time = format_time(slot.get("start_time"))
            end_time = format_time(slot.get("end_time"))

            start_datetime = f"{date_str}T{start_time}:00"
            end_datetime = f"{date_str}T{end_time}:00"
            summary_text = f"{slot.get('subject')} Class"

            events_result = (
                calendar_service.events()
                .list(
                    calendarId="primary",
                    timeMin=f"{date_str}T00:00:00+05:30",
                    timeMax=f"{date_str}T23:59:59+05:30",
                    singleEvents=True,
                    q=summary_text,
                )
                .execute()
            )

            existing_events = events_result.get("items", [])
            is_duplicate = any(event.get("summary") == summary_text for event in existing_events)

            if is_duplicate:
                current_app.logger.info("Skipping duplicate event: %s on %s", summary_text, date_str)
                continue

            meet_link = slot.get("meet_link")
            description = "ClassOps Auto-synced Student Class"
            if meet_link:
                description += f"\n\nJoin Class via Meet: {meet_link}"

            event = {
                "summary": summary_text,
                "description": description,
                "start": {
                    "dateTime": start_datetime,
                    "timeZone": "Asia/Kolkata",
                },
                "end": {
                    "dateTime": end_datetime,
                    "timeZone": "Asia/Kolkata",
                },
                "recurrence": ["RRULE:FREQ=WEEKLY"],
            }

            if meet_link:
                event["location"] = meet_link

            calendar_service.events().insert(calendarId="primary", body=event).execute()
            synced_count += 1
        except Exception as exc:
            current_app.logger.error("Failed to sync slot %s: %s", slot.get("id"), exc)

    return jsonify({"message": f"Successfully synced {synced_count} classes to your Google Calendar."})


def submit_evaluation():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    course_id = data.get("course_id")
    ratings = data.get("ratings")

    if not course_id or not ratings:
        return jsonify({"error": "Missing course_id or ratings"}), 400

    student_id = session["user"].get("id")
    if not student_id:
        return jsonify({"error": "Student ID missing from session"}), 400

    eval_data = {
        "course_id": course_id,
        "student_id": student_id,
        "student_email": session["user"].get("email"),
        "ratings": ratings,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        db.put_evaluation(course_id, student_id, eval_data)
        return jsonify({"success": True, "message": "Evaluation submitted successfully"})
    except Exception as exc:
        current_app.logger.exception("Failed to submit evaluation: %s", exc)
        return jsonify({"error": "Database error"}), 500


def get_evaluations(course_id):
    if "user" not in session or session["user"].get("role") != "teacher":
        return jsonify({"error": "Unauthorized"}), 403

    teacher = get_authenticated_teacher()
    if not teacher:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        evaluations = db.get_evaluations_by_course(course_id)

        if not evaluations:
            return jsonify({"evaluations": [], "averages": {}})

        averages = {}
        counts = {}
        for evaluation in evaluations:
            ratings = evaluation.get("ratings", {})
            for key, value in ratings.items():
                averages[key] = averages.get(key, 0) + value
                counts[key] = counts.get(key, 0) + 1

        for key in averages:
            averages[key] = round(averages[key] / counts[key], 2)

        return jsonify(
            {
                "evaluations": evaluations,
                "averages": averages,
            }
        )
    except Exception as exc:
        current_app.logger.exception("Failed to get evaluations: %s", exc)
        return jsonify({"error": "Database error"}), 500


def download_evaluations(course_id):
    if "user" not in session or session["user"].get("role") != "teacher":
        return jsonify({"error": "Unauthorized"}), 403

    try:
        evaluations = db.get_evaluations_by_course(course_id)

        output_buffer = io.StringIO()
        writer = csv.writer(output_buffer)
        questions = [
            "Q1",
            "Q2",
            "Q3",
            "Q4",
            "Q5",
            "Q6",
            "Q7",
            "Q8",
            "Q9",
            "Q10",
        ]
        headers = ["Student Email", "Timestamp"] + questions
        writer.writerow(headers)

        for evaluation in evaluations:
            row = [evaluation.get("student_email", "Unknown"), evaluation.get("timestamp", "")]
            ratings = evaluation.get("ratings", {})
            for question in questions:
                row.append(ratings.get(question, ""))
            writer.writerow(row)

        output = make_response(output_buffer.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename=course_{course_id}_evaluations.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    except Exception as exc:
        current_app.logger.exception("Failed to generate CSV: %s", exc)
        return jsonify({"error": "Failed to generate CSV"}), 500
