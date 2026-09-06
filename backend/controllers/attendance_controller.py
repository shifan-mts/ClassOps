from datetime import datetime, timezone

from flask import jsonify, request

from repositories import dynamodb_repository as db


def get_attendance():
    course_id = request.args.get("course_id")
    date_str = request.args.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    if not course_id:
        return jsonify({"error": "course_id is required"}), 400

    datetime.strptime(date_str, "%Y-%m-%d").date()
    records = db.get_attendance_records(course_id, date_str)

    return (
        jsonify(
            {
                "records": {record.get("student_id"): record.get("status") for record in records},
                "date": date_str,
                "course_id": course_id,
            }
        ),
        200,
    )


def mark_attendance():
    data = request.json
    course_id = data.get("course_id")
    date_str = data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    datetime.strptime(date_str, "%Y-%m-%d").date()

    if not course_id or "records" not in data:
        return jsonify({"error": "course_id and records are required"}), 400

    for record in data["records"]:
        new_record = {
            "student_id": record["student_id"],
            "course_id": course_id,
            "status": record["status"],
            "date": date_str,
        }
        db.put_attendance_record(course_id, new_record)

    return jsonify({"message": "Attendance recorded successfully"}), 200


def get_attendance_report(course_id):
    students = db.get_students_by_course(course_id)
    all_attendance = db.get_attendance_records(course_id)
    report = []

    for student in students:
        student_id = student.get("id")
        roll_number = student.get("roll_number")

        student_attendance = [
            record
            for record in all_attendance
            if str(record.get("student_id")) == str(student_id)
            or (roll_number and str(record.get("student_id")) == str(roll_number))
        ]

        total_classes = len(student_attendance)
        present_count = len([record for record in student_attendance if record.get("status") == "Present"])

        percentage = (present_count / total_classes * 100) if total_classes > 0 else 0

        report.append(
            {
                "student_id": student_id,
                "name": student.get("name"),
                "roll_number": roll_number,
                "total": total_classes,
                "present": present_count,
                "percentage": round(percentage, 2),
            }
        )

    return jsonify(report), 200
