import os
import uuid
from datetime import datetime, timezone

from flask import current_app, jsonify, request

from config.constants import BACKEND_DIR, WEEKDAYS
from repositories import dynamodb_repository as db
from services.teacher_service import (
    get_authenticated_teacher,
    get_owned_course_or_404,
    normalize_period_timings,
)
from utils.api_key import normalize_api_key


def teacher_profile():
    teacher = get_authenticated_teacher()
    if not teacher:
        return jsonify({"error": "Teacher not found or not authenticated"}), 401

    if request.method == "POST":
        data = request.json
        if "availability" in data:
            teacher["availability"] = data["availability"]
        if "period_timings" in data:
            teacher["period_timings"] = normalize_period_timings(data["period_timings"])
        if "name" in data:
            teacher["name"] = data["name"]

        db.put_teacher(teacher)

        if "courses" in data:
            for course_data in data["courses"]:
                course = db.get_course(teacher["email"], course_data["id"])
                if course:
                    try:
                        parsed_hours = int(course_data.get("hours", course.get("hours_per_week", 0)))
                    except (TypeError, ValueError):
                        parsed_hours = course.get("hours_per_week", 0)
                    course["hours_per_week"] = max(parsed_hours, 0)
                    db.put_course(teacher["email"], course)

        return jsonify({"message": "Profile updated successfully"})

    courses = db.get_courses_by_teacher(teacher["email"])
    return jsonify(
        {
            "name": teacher.get("name", ""),
            "availability": teacher.get("availability", {}) or {day: [] for day in WEEKDAYS},
            "period_timings": normalize_period_timings(teacher.get("period_timings", [])),
            "courses": [
                {
                    "id": course.get("id"),
                    "name": course.get("name"),
                    "hours": course.get("hours_per_week", 0),
                }
                for course in courses
            ],
        }
    )


def generate_timetable():
    from scheduler import run_backtracking_scheduler

    teacher = get_authenticated_teacher()
    if not teacher:
        return jsonify({"error": "Teacher not found or not authenticated"}), 401

    availability = teacher.get("availability", {}) or {}
    courses = db.get_courses_by_teacher(teacher["email"])
    courses_to_schedule = []
    for course in courses:
        hours = max(int(course.get("hours_per_week", 0) or 0), 0)
        if hours <= 0:
            continue
        courses_to_schedule.append(
            {
                "id": course.get("id"),
                "name": course.get("name"),
                "hours": hours,
            }
        )

    if not courses_to_schedule:
        return jsonify({"error": "No active timetable classes found. Set hours greater than 0 for current classes."}), 400

    new_slots = run_backtracking_scheduler(availability, courses_to_schedule)

    if new_slots is None:
        return jsonify({"error": "Could not generate a feasible timetable. Try increasing availability."}), 400

    for course in courses:
        old_slots = db.get_timetable_slots_by_course(course["id"])
        for slot in old_slots:
            db.delete_timetable_slot(course["id"], slot["id"])

    for slot in new_slots:
        timetable_slot = {
            "id": str(uuid.uuid4()),
            "day": slot["day"],
            "period": slot["period"],
            "course_id": slot["course_id"],
            "subject": slot["subject"],
        }
        db.put_timetable_slot(slot["course_id"], timetable_slot)

    return jsonify({"message": "Timetable generated and saved."})


def get_timetable():
    teacher = get_authenticated_teacher()
    if not teacher:
        return jsonify({"error": "Teacher not found or not authenticated"}), 401

    availability = teacher.get("availability", {}) or {day: [] for day in WEEKDAYS}
    period_timings = teacher.get("period_timings", [])
    courses = db.get_courses_by_teacher(teacher["email"])

    result = {}
    for course in courses:
        if max(int(course.get("hours_per_week", 0) or 0), 0) <= 0:
            continue
        result[str(course["id"])] = {day: {} for day in WEEKDAYS}

    all_slots = []
    seen_teacher_slots = set()
    for course in courses:
        slots = db.get_timetable_slots_by_course(course["id"])
        for slot in slots:
            signature = f"{course['id']}_{slot.get('day')}_{slot.get('period')}"
            if signature not in seen_teacher_slots:
                seen_teacher_slots.add(signature)
                slot["course"] = course
                all_slots.append(slot)

    target_date_str = request.args.get("date")
    is_today = request.args.get("today") == "true"

    target_day_name = None
    if is_today:
        target_day_name = datetime.now(timezone.utc).strftime("%A")
    elif target_date_str:
        try:
            target_day_name = datetime.strptime(target_date_str, "%Y-%m-%d").strftime("%A")
        except ValueError:
            pass

    if target_day_name:
        all_slots = [slot for slot in all_slots if slot.get("day") == target_day_name]

    for slot in all_slots:
        if "period" in slot:
            try:
                slot["period"] = int(slot["period"])
            except (TypeError, ValueError):
                slot["period"] = 0

        if "year" in slot:
            try:
                slot["year"] = int(slot["year"])
            except (TypeError, ValueError):
                slot["year"] = None

    all_slots.sort(key=lambda slot: (str(slot.get("day", "")), slot.get("period", 0)))

    for slot in all_slots:
        cid_str = str(slot["course_id"])
        day_str = str(slot.get("day", "Monday"))
        period_str = str(slot["period"])

        if cid_str not in result:
            result[cid_str] = {day: {} for day in WEEKDAYS}

        if day_str not in result[cid_str]:
            result[cid_str][day_str] = {}

        course = slot["course"]
        result[cid_str][day_str][period_str] = {
            "slot_id": str(slot.get("id", "")),
            "course_id": cid_str,
            "sub": str(slot.get("subject", "")),
            "className": str(course.get("name", "")),
            "meetLink": course.get("meet_link"),
            "meetingCode": course.get("meet_code"),
        }

    return jsonify(
        {
            "timetable": result,
            "availability": availability,
            "period_timings": normalize_period_timings(period_timings),
        }
    )


def upsert_timetable_slot():
    teacher = get_authenticated_teacher()
    if not teacher:
        return jsonify({"error": "Teacher not found or not authenticated"}), 401

    data = request.json or {}
    day = data.get("day")
    try:
        period = int(data.get("period"))
    except (TypeError, ValueError):
        return jsonify({"error": "period must be an integer"}), 400

    if day not in WEEKDAYS:
        return jsonify({"error": "Invalid day"}), 400

    course_id = data.get("course_id")
    courses = db.get_courses_by_teacher(teacher["email"])

    existing_slot_course_id = None
    existing_slot = None
    for course in courses:
        slots = db.get_timetable_slots_by_course(course["id"])
        for slot in slots:
            if slot.get("day") == day and slot.get("period") == period:
                existing_slot = slot
                existing_slot_course_id = course["id"]
                break
        if existing_slot:
            break

    if not course_id:
        if existing_slot:
            db.delete_timetable_slot(existing_slot_course_id, existing_slot["id"])
        return jsonify({"message": "Timetable slot cleared."}), 200

    course = get_owned_course_or_404(course_id)
    if not course:
        return jsonify({"error": "Invalid course"}), 400
    if max(int(course.get("hours_per_week", 0) or 0), 0) <= 0:
        return jsonify({"error": "This class is inactive. Set hours above 0 before assigning it."}), 400

    if existing_slot:
        if str(existing_slot_course_id) != str(course_id):
            db.delete_timetable_slot(existing_slot_course_id, existing_slot["id"])
            new_slot = {
                "id": str(uuid.uuid4()),
                "day": day,
                "period": period,
                "course_id": course_id,
                "subject": course.get("name"),
            }
            db.put_timetable_slot(course_id, new_slot)
        else:
            existing_slot["subject"] = course.get("name")
            db.put_timetable_slot(course_id, existing_slot)
    else:
        new_slot = {
            "id": str(uuid.uuid4()),
            "day": day,
            "period": period,
            "course_id": course_id,
            "subject": course.get("name"),
        }
        db.put_timetable_slot(course_id, new_slot)

    return jsonify({"message": "Timetable slot updated."}), 200


def update_api_key():
    data = request.json
    new_key = normalize_api_key(data.get("api_key"))
    if not new_key:
        return jsonify({"error": "No API key provided"}), 400

    env_path = os.path.join(BACKEND_DIR, ".env")
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r") as env_file:
                lines = env_file.readlines()

        key_found = False
        new_lines = []
        for line in lines:
            if line.startswith("GEMINI_API_KEY="):
                new_lines.append(f"GEMINI_API_KEY={new_key}\n")
                key_found = True
            else:
                new_lines.append(line)

        if not key_found:
            new_lines.append(f"GEMINI_API_KEY={new_key}\n")

        with open(env_path, "w") as env_file:
            env_file.writelines(new_lines)

        from controllers import qp_controller

        qp_controller.GEMINI_API_KEY = new_key
        os.environ["GEMINI_API_KEY"] = new_key

        return jsonify({"message": "API Key updated successfully in .env and server memory."})
    except Exception as exc:
        current_app.logger.exception("Failed to update .env")
        return jsonify({"error": f"Failed to update .env: {str(exc)}"}), 500
