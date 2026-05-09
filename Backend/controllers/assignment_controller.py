from datetime import datetime, timezone

from flask import current_app, jsonify, request

from ai_checker import analyze_text, handle_upload
from repositories import dynamodb_repository as db
from services.google_service import get_classroom_service
from services.teacher_service import get_owned_course_or_404


def sync_assignments(course_id):
    service = get_classroom_service()
    if not service:
        return jsonify({"error": "Not authenticated"}), 401

    course = get_owned_course_or_404(course_id)
    if not course.get("google_course_id"):
        return jsonify({"error": "Course not linked to Google Classroom"}), 400

    try:
        results = service.courses().courseWork().list(courseId=course["google_course_id"]).execute()
        coursework_data = results.get("courseWork", [])

        count = 0
        for coursework in coursework_data:
            existing = db.get_assignment(course_id, coursework["id"])
            if not existing:
                new_assignment = {
                    "id": coursework["id"],
                    "google_assignment_id": coursework["id"],
                    "title": coursework["title"],
                    "description": coursework.get("description"),
                    "due_date": coursework.get("dueDate"),
                    "course_id": course_id,
                }
                db.put_assignment(course_id, new_assignment)
                count += 1
        return jsonify({"message": f"Synced {count} new assignments successfully"}), 200
    except Exception as exc:
        current_app.logger.exception("Assignment sync failed: %s", exc)
        return jsonify({"error": f"Classroom API error: {str(exc)}"}), 500


def get_assignments(course_id):
    assignments = db.get_assignments_by_course(course_id)
    return jsonify(
        [
            {
                "id": assignment.get("id"),
                "google_assignment_id": assignment.get("google_assignment_id"),
                "title": assignment.get("title"),
            }
            for assignment in assignments
        ]
    )


def check_plagiarism():
    if "file" in request.files:
        file = request.files["file"]
        if not file or not file.filename:
            return jsonify({"error": "No file uploaded"}), 400
        result = handle_upload(file)
        status_code = 200 if result.get("success") else 500
        return jsonify(result), status_code

    data = request.get_json(silent=True) or {}
    text_to_check = data.get("text")
    if text_to_check:
        result = analyze_text(text_to_check)
        status_code = 200 if result.get("success") else 500
        return jsonify(result), status_code

    return jsonify({"error": "Provide a file upload or a text field."}), 400


def get_submissions(course_id, assignment_id):
    service = get_classroom_service()
    if not service:
        return jsonify({"error": "Not authenticated with Google"}), 401

    course = get_owned_course_or_404(course_id)
    google_course_id = course.get("google_course_id")
    assignment = db.get_assignment(course_id, assignment_id)
    if not assignment or not google_course_id:
        return jsonify({"error": "Assignment or course not found"}), 404

    google_assignment_id = assignment.get("google_assignment_id")

    try:
        results = (
            service.courses()
            .courseWork()
            .studentSubmissions()
            .list(courseId=google_course_id, courseWorkId=google_assignment_id)
            .execute()
        )
        submissions = results.get("studentSubmissions", [])

        students = db.get_students_by_course(course_id)
        student_map = {student.get("id"): student for student in students if student.get("id")}

        enhanced_submissions = []
        for submission in submissions:
            user_id = submission.get("userId")
            student = student_map.get(user_id, {})
            feedback = db.get_feedback(course_id, assignment_id, user_id) or {}

            enhanced_submissions.append(
                {
                    "id": submission.get("id"),
                    "userId": user_id,
                    "name": student.get("name", "Unknown Student"),
                    "roll_number": student.get("roll_number"),
                    "state": submission.get("state"),
                    "assignedGrade": submission.get("assignedGrade"),
                    "internal_comment": feedback.get("internal_comment", ""),
                    "synced_comment": feedback.get("synced_comment", ""),
                }
            )

        return jsonify(enhanced_submissions)
    except Exception as exc:
        current_app.logger.error("Error fetching submissions: %s", exc)
        return jsonify({"error": str(exc)}), 500


def save_feedback(course_id, assignment_id, student_id):
    service = get_classroom_service()
    if not service:
        return jsonify({"error": "Not authenticated with Google"}), 401

    data = request.json
    internal_comment = data.get("internal_comment", "")
    grade = data.get("grade")
    sync_to_google = data.get("sync_to_google", False)
    google_submission_id = data.get("google_submission_id")

    course = get_owned_course_or_404(course_id)
    google_course_id = course.get("google_course_id")
    assignment = db.get_assignment(course_id, assignment_id)
    google_assignment_id = assignment.get("google_assignment_id") if assignment else None

    synced_comment = ""

    if sync_to_google and google_course_id and google_assignment_id and google_submission_id:
        try:
            if grade is not None:
                (
                    service.courses()
                    .courseWork()
                    .studentSubmissions()
                    .patch(
                        courseId=google_course_id,
                        courseWorkId=google_assignment_id,
                        id=google_submission_id,
                        updateMask="assignedGrade",
                        body={"assignedGrade": float(grade)},
                    )
                    .execute()
                )

            synced_comment = internal_comment

        except Exception as exc:
            current_app.logger.error("Error syncing to Google: %s", exc)
            return jsonify({"error": f"Failed to sync to Google Classroom: {str(exc)}"}), 500

    feedback_data = {
        "internal_comment": internal_comment,
        "synced_comment": synced_comment,
        "grade": grade,
        "google_submission_id": google_submission_id,
        "last_synced": datetime.now(timezone.utc).isoformat() if sync_to_google else None,
    }
    db.put_feedback(course_id, assignment_id, student_id, feedback_data)

    return jsonify({"message": "Feedback saved successfully", "feedback": feedback_data})


def analyze_submissions(course_id, assignment_id):
    from ai_checker import run_batch_analysis

    service = get_classroom_service()
    if not service:
        return jsonify({"error": "Not authenticated with Google Classroom"}), 401

    assignment = db.get_assignment(course_id, assignment_id)
    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    course = get_owned_course_or_404(course_id)

    try:
        results = (
            service.courses()
            .courseWork()
            .studentSubmissions()
            .list(
                courseId=course.get("google_course_id"),
                courseWorkId=assignment.get("google_assignment_id"),
            )
            .execute()
        )
        submissions = results.get("studentSubmissions", [])

        if not submissions:
            return jsonify({"message": "No submissions found to analyze.", "results": [], "alerts": []}), 200

        local_students = db.get_students_by_course(course_id)
        student_map = {student.get("roll_number"): student.get("name") for student in local_students}

        batch_input = []
        for submission in submissions[:15]:
            uid = submission.get("userId")
            name = student_map.get(uid, f"Student {uid}")

            content = ""
            file_info = ""

            if "shortAnswerSubmission" in submission:
                content = submission["shortAnswerSubmission"].get("answer", "")

            elif "assignmentSubmission" in submission and "attachments" in submission["assignmentSubmission"]:
                attachments = submission["assignmentSubmission"]["attachments"]
                file_names = []
                for attachment in attachments:
                    if "driveFile" in attachment:
                        file_names.append(attachment["driveFile"].get("title", "Untitled"))

                if file_names:
                    file_info = f" [Files: {', '.join(file_names)}]"
                    content = (
                        f"Note: This student submitted files ({', '.join(file_names)}). "
                        "Automated analysis for Google Drive files is currently disabled (requires Drive API)."
                    )

            if not content or content.strip() == "":
                content = ""
                file_info = " [No Submission]"

            batch_input.append(
                {
                    "name": name + file_info,
                    "content": content,
                }
            )

        analysis_data = run_batch_analysis(batch_input)

        formatted_results = []
        for result in analysis_data["ai_results"]:
            formatted_results.append(
                {
                    "name": result["name"],
                    "ai_score": result["ai_score"],
                    "status": result["status"],
                }
            )

        formatted_alerts = []
        formatted_plagiarism = []
        for plagiarism in analysis_data["plagiarism_results"]:
            formatted_plagiarism.append(
                {
                    "name": plagiarism["name"],
                    "status": plagiarism["status"],
                    "matched_with": plagiarism.get("matched_with", "N/A"),
                    "score": plagiarism.get("highest_match_percent", 0),
                }
            )

            if "?" in plagiarism["status"]:
                formatted_alerts.append(
                    {
                        "students": [plagiarism["name"], plagiarism["matched_with"]],
                        "score": plagiarism["highest_match_percent"],
                    }
                )

        return jsonify(
            {
                "success": True,
                "results": formatted_results,
                "plagiarism": formatted_plagiarism,
                "alerts": formatted_alerts,
                "submission_count": len(submissions),
            }
        )

    except Exception as exc:
        current_app.logger.exception("Analysis failed: %s", exc)
        return jsonify({"error": f"Analysis failed: {str(exc)}"}), 500
