import uuid

from flask import jsonify, request

from repositories import dynamodb_repository as db
from services.teacher_service import get_owned_course_or_404


def manage_targets():
    if request.method == "POST":
        data = request.json or {}
        if not data.get("topic") or not data.get("date") or not data.get("course_id"):
            return jsonify({"error": "topic, date, and course_id are required"}), 400

        course_id = data["course_id"]
        new_target = {
            "id": str(uuid.uuid4()),
            "topic": data["topic"],
            "target_date": data["date"],
            "is_completed": False,
            "course_id": course_id,
        }
        db.put_material_target(course_id, new_target)

        course = get_owned_course_or_404(course_id)
        return (
            jsonify(
                {
                    "id": new_target["id"],
                    "topic": new_target["topic"],
                    "completed": new_target["is_completed"],
                    "date": new_target["target_date"],
                    "course_id": new_target["course_id"],
                    "course_name": course.get("name") if course else None,
                }
            ),
            201,
        )

    course_id = request.args.get("course_id")
    if not course_id:
        return jsonify({"error": "course_id is required"}), 400

    targets = db.get_material_targets_by_course(course_id)
    targets = sorted(targets, key=lambda target: target.get("target_date", ""))
    course = get_owned_course_or_404(course_id)

    return jsonify(
        [
            {
                "id": target.get("id"),
                "topic": target.get("topic"),
                "completed": target.get("is_completed"),
                "date": target.get("target_date"),
                "course_id": target.get("course_id"),
                "course_name": course.get("name") if course else None,
            }
            for target in targets
        ]
    )


def update_target(course_id, target_id):
    data = request.json or {}

    targets = db.get_material_targets_by_course(course_id)
    target = next((item for item in targets if str(item.get("id")) == str(target_id)), None)

    if not target:
        return jsonify({"error": "Target not found"}), 404

    if "topic" in data and data["topic"]:
        target["topic"] = data["topic"]
    if "date" in data and data["date"]:
        target["target_date"] = data["date"]
    if "completed" in data:
        target["is_completed"] = bool(data["completed"])

    db.put_material_target(course_id, target)
    course = get_owned_course_or_404(course_id)

    return (
        jsonify(
            {
                "id": target["id"],
                "topic": target["topic"],
                "completed": target["is_completed"],
                "date": target["target_date"],
                "course_id": target["course_id"],
                "course_name": course.get("name") if course else None,
            }
        ),
        200,
    )
