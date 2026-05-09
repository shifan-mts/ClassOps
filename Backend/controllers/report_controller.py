from datetime import datetime
from io import BytesIO
from textwrap import wrap

from flask import jsonify, request, send_file

from services.report_service import collect_report_data, compute_compliance_metrics


def get_compliance_metrics():
    course_id = request.args.get("course_id")
    if course_id:
        try:
            course_id = int(course_id)
        except ValueError:
            return jsonify({"error": "course_id must be an integer"}), 400

    metrics = compute_compliance_metrics(course_id)
    return jsonify(metrics), 200


def generate_compliance_report():
    course_id = request.args.get("course_id")
    if course_id:
        try:
            course_id = int(course_id)
        except ValueError:
            return jsonify({"error": "course_id must be an integer"}), 400

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except Exception:
        return jsonify({"error": "PDF generation requires reportlab. Install it and restart the backend."}), 500

    metrics = compute_compliance_metrics(course_id)
    data = collect_report_data(course_id)
    student_map = {student.get("id", student.get("roll_number")): student for student in data["students"]}
    course_map = {course.get("id"): course for course in data["courses"]}

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    x = 40
    y = height - 40

    def write_line(line):
        nonlocal y
        for chunk in wrap(str(line), width=95) or [""]:
            if y < 40:
                pdf.showPage()
                y = height - 40
            pdf.drawString(x, y, chunk)
            y -= 14

    write_line("ClassOps NBA/NAAC Compliance Report")
    write_line(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if course_id and data["courses"]:
        write_line(f"Course: {data['courses'][0].get('name')}")
    write_line("")

    write_line("Compliance Metrics")
    write_line(f"CO Coverage: {metrics['co_coverage']}%")
    write_line(f"PO Mapping: {metrics['po_mapping']}%")
    write_line(f"Status: {metrics['status']}")
    write_line("")

    write_line("Courses")
    if data["courses"]:
        for course in data["courses"]:
            write_line(f"- {course.get('name')} (ID: {course.get('id')})")
    else:
        write_line("No courses found.")
    write_line("")

    write_line("Students")
    if data["students"]:
        for student in data["students"]:
            course = course_map.get(student.get("course_id"))
            course_name = course.get("name") if course else f"Course {student.get('course_id')}"
            write_line(f"- {student.get('name')} ({student.get('roll_number')}) | {course_name}")
    else:
        write_line("No students found.")
    write_line("")

    write_line("Syllabus Targets")
    if data["targets"]:
        for target in data["targets"]:
            status = "Completed" if target.get("is_completed") else "Pending"
            course = course_map.get(target.get("course_id"))
            course_name = course.get("name") if course else ""
            write_line(f"- {target.get('topic')} | Due: {target.get('target_date')} | {status} | {course_name}")
    else:
        write_line("No targets found.")
    write_line("")

    write_line("Attendance Summary")
    if data["attendance_summary"]:
        for entry in data["attendance_summary"]:
            write_line(
                f"- {entry['name']} ({entry['roll_number']}): "
                f"{entry['percentage']}% ({entry['present_count']}/{entry['total_classes']})"
            )
    else:
        write_line("No attendance data found.")
    write_line("")

    write_line("Attendance Records")
    if data["attendance_records"]:
        for record in data["attendance_records"]:
            student = student_map.get(record.get("student_id"))
            course = course_map.get(record.get("course_id"))
            student_label = (
                f"{student.get('name')} ({student.get('roll_number')})"
                if student
                else f"Student {record.get('student_id')}"
            )
            course_label = course.get("name") if course else f"Course {record.get('course_id')}"
            write_line(f"- {record.get('date')} | {student_label} | {course_label} | {record.get('status')}")
    else:
        write_line("No attendance records found.")
    write_line("")

    write_line("Assignments")
    if data["assignments"]:
        for assignment in data["assignments"]:
            write_line(f"- {assignment.get('title')} (Course ID: {assignment.get('course_id')})")
    else:
        write_line("No assignments found.")
    write_line("")

    write_line("Timetable")
    if data["timetable_slots"]:
        for slot in data["timetable_slots"]:
            course = course_map.get(slot.get("course_id"))
            course_name = course.get("name") if course else ""
            write_line(f"- {slot.get('day')} P{slot.get('period') + 1}: {slot.get('subject')} ({course_name})")
    else:
        write_line("No timetable slots found.")

    pdf.save()
    buffer.seek(0)

    filename = "nba_compliance_report.pdf"
    if course_id and data["courses"]:
        safe_name = "_".join(data["courses"][0].get("name", "").lower().split())
        filename = f"nba_compliance_report_{safe_name}.pdf"

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )
