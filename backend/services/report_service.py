from repositories import dynamodb_repository as db
from services.teacher_service import get_owned_course_or_404


def compute_compliance_metrics(course_id=None):
    if not course_id:
        return {
            "co_coverage": 0,
            "po_mapping": 0,
            "status": "Select a course",
            "completed_targets": 0,
            "pending_targets": 0,
            "total_targets": 0,
            "attendance_records": 0,
            "present_records": 0,
        }

    targets = db.get_material_targets_by_course(course_id)
    attendance = db.get_attendance_records(course_id)

    total_targets = len(targets)
    completed_targets = len([target for target in targets if target.get("is_completed")])
    pending_targets = max(0, total_targets - completed_targets)
    co_coverage = round((completed_targets / total_targets) * 100) if total_targets else 0

    total_attendance = len(attendance)
    present_count = len([record for record in attendance if record.get("status") == "Present"])
    po_mapping = round((present_count / total_attendance) * 100) if total_attendance else 0

    if total_targets == 0:
        status = "No targets yet"
    else:
        status = "On track" if completed_targets >= pending_targets else "Needs attention"

    return {
        "co_coverage": co_coverage,
        "po_mapping": po_mapping,
        "status": status,
        "completed_targets": completed_targets,
        "pending_targets": pending_targets,
        "total_targets": total_targets,
        "attendance_records": total_attendance,
        "present_records": present_count,
    }


def collect_report_data(course_id=None):
    if not course_id:
        return {
            "courses": [],
            "students": [],
            "targets": [],
            "assignments": [],
            "timetable_slots": [],
            "attendance_summary": [],
            "attendance_records": [],
        }

    course = get_owned_course_or_404(course_id)
    courses = [course] if course else []
    students = db.get_students_by_course(course_id)
    targets = db.get_material_targets_by_course(course_id)
    assignments = db.get_assignments_by_course(course_id)
    slots = db.get_timetable_slots_by_course(course_id)
    attendance_records = db.get_attendance_records(course_id)

    attendance_summary = []
    for student in students:
        roll = student.get("roll_number")
        student_attendance = [record for record in attendance_records if record.get("student_id") == roll]
        total_classes = len(student_attendance)
        present_count = len([record for record in student_attendance if record.get("status") == "Present"])
        percentage = round((present_count / total_classes) * 100, 1) if total_classes else 0
        attendance_summary.append(
            {
                "name": student.get("name"),
                "roll_number": roll,
                "course_id": course_id,
                "total_classes": total_classes,
                "present_count": present_count,
                "percentage": percentage,
            }
        )

    return {
        "courses": courses,
        "students": students,
        "targets": targets,
        "assignments": assignments,
        "timetable_slots": slots,
        "attendance_summary": attendance_summary,
        "attendance_records": attendance_records,
    }
