import csv
import io
import json

from flask import current_app, jsonify, make_response, request, session

from services.google_service import (
    build_meet_export_rows,
    get_attendance_report,
    get_meeting_link,
    get_missing_scopes,
)
from services.teacher_service import get_owned_course_or_404
from utils.meet_helpers import normalize_meeting_code


def get_course_meet_attendance(course_id):
    if "user" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    course = get_owned_course_or_404(course_id)
    if not course:
        return jsonify({"error": "Forbidden"}), 403

    missing_scopes = get_missing_scopes(
        "https://www.googleapis.com/auth/classroom.profile.emails",
        "https://www.googleapis.com/auth/meetings.space.readonly",
    )
    if missing_scopes:
        return (
            jsonify(
                {
                    "error": "Please sign in with Google again to grant the Meet attendance scopes.",
                    "missing_scopes": missing_scopes,
                }
            ),
            400,
        )

    requested_code = request.args.get("meeting_code")
    resolved = get_meeting_link(course_id)
    meeting_code = normalize_meeting_code(requested_code) or resolved.get("meetingCode")
    if not meeting_code:
        return (
            jsonify(
                {
                    "error": "No Google Meet code is configured for this course yet.",
                    "meeting": resolved,
                }
            ),
            400,
        )

    try:
        report = get_attendance_report(meeting_code, course_id=course_id)
        report["meeting"] = resolved
        return jsonify(report), 200
    except Exception as exc:
        current_app.logger.exception("Failed to fetch Meet attendance report: %s", exc)
        return (
            jsonify(
                {
                    "meeting": resolved,
                    "meetingCode": meeting_code,
                    "conferenceRecord": None,
                    "conferenceStartTime": None,
                    "conferenceEndTime": None,
                    "meetingEnded": False,
                    "livePresentCount": 0,
                    "participantCount": 0,
                    "attendance": [],
                    "unmatchedParticipants": [],
                    "allParticipants": [],
                    "presentStudentIds": [],
                    "status": "unavailable",
                    "message": str(exc),
                }
            ),
            200,
        )


def export_course_meet_attendance(course_id):
    if "user" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    course = get_owned_course_or_404(course_id)
    if not course:
        return jsonify({"error": "Forbidden"}), 403

    missing_scopes = get_missing_scopes(
        "https://www.googleapis.com/auth/classroom.profile.emails",
        "https://www.googleapis.com/auth/meetings.space.readonly",
    )
    if missing_scopes:
        return (
            jsonify(
                {
                    "error": "Please sign in with Google again to grant the Meet attendance scopes.",
                    "missing_scopes": missing_scopes,
                }
            ),
            400,
        )

    requested_code = request.args.get("meeting_code")
    export_format = (request.args.get("format") or "json").strip().lower()
    resolved = get_meeting_link(course_id)
    meeting_code = normalize_meeting_code(requested_code) or resolved.get("meetingCode")
    if not meeting_code:
        return jsonify({"error": "No Google Meet code is configured for this course yet."}), 400

    try:
        report = get_attendance_report(meeting_code, course_id=course_id)
        export_rows = build_meet_export_rows(report)

        if export_format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "studentName",
                    "rollNumber",
                    "email",
                    "joinTime",
                    "leaveTime",
                    "totalDurationMinutes",
                    "sessionCount",
                    "rejoinCount",
                    "activeNow",
                ],
            )
            writer.writeheader()
            writer.writerows(export_rows)

            response = make_response(output.getvalue())
            response.headers["Content-Type"] = "text/csv; charset=utf-8"
            response.headers["Content-Disposition"] = f"attachment; filename=meet_attendance_course_{course_id}_{meeting_code}.csv"
            return response

        payload = {
            "meeting": resolved,
            "summary": {
                "meetingCode": report.get("meetingCode"),
                "conferenceRecord": report.get("conferenceRecord"),
                "conferenceStartTime": report.get("conferenceStartTime"),
                "conferenceEndTime": report.get("conferenceEndTime"),
                "meetingEnded": report.get("meetingEnded"),
                "participantCount": report.get("participantCount"),
                "livePresentCount": report.get("livePresentCount"),
            },
            "attendance": export_rows,
            "unmatchedParticipants": report.get("unmatchedParticipants") or [],
        }
        response = make_response(json.dumps(payload, indent=2))
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        response.headers["Content-Disposition"] = f"attachment; filename=meet_attendance_course_{course_id}_{meeting_code}.json"
        return response
    except Exception as exc:
        current_app.logger.exception("Failed to export Meet attendance report: %s", exc)
        return jsonify({"error": str(exc)}), 500
