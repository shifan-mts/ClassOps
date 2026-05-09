import os
from datetime import datetime

from flask import current_app, jsonify, request, send_file, session
from googleapiclient.http import MediaIoBaseUpload

from config.constants import GEMINI_MODEL
from services.google_service import get_drive_service
from utils.api_key import normalize_api_key
from utils.qp_helpers import (
    build_qp_prompt,
    build_question_paper_docx,
    extract_json_object,
    get_qp_header,
    get_qp_schema,
    normalize_qp,
    parse_qp_json,
    render_qp_text,
)

GEMINI_API_KEY = normalize_api_key(os.getenv("GEMINI_API_KEY"))


def generate_question_paper():
    data = request.get_json(silent=True) or {}
    topic = (data.get("topic") or "").strip()
    if not topic:
        return jsonify({"error": "topic is required"}), 400

    difficulty = data.get("difficulty", "Medium")
    course_name = data.get("course_name", "General Course")
    output = data.get("output", "text")

    part_a_count = 5
    part_b_count = 2
    part_c_count = 1

    header = get_qp_header(data, course_name)

    custom_key = normalize_api_key(data.get("api_key"))
    env_key = normalize_api_key(GEMINI_API_KEY) or normalize_api_key(os.getenv("GEMINI_API_KEY"))
    effective_key = custom_key if custom_key else env_key

    if not effective_key:
        return jsonify({"error": "Gemini API key is missing. Please provide one in the input box below."}), 400

    prompt = build_qp_prompt(topic, course_name, difficulty, part_a_count, part_b_count, part_c_count)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=effective_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=900,
                response_mime_type="application/json",
                response_schema=get_qp_schema(part_a_count, part_b_count, part_c_count),
            ),
        )
    except ImportError:
        return jsonify({"error": "google-genai is not installed. Question paper generation is disabled."}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    try:
        raw_text = ""
        if response is not None:
            raw_text = getattr(response, "text", "") or ""

        qp = getattr(response, "parsed", None)
        if not qp:
            qp = parse_qp_json(raw_text)
        if not qp:
            qp = parse_qp_json(extract_json_object(raw_text))
        qp = normalize_qp(qp, part_a_count, part_b_count, part_c_count)
        if not qp:
            if output == "text":
                return jsonify({"question_paper": raw_text})
            return (
                jsonify(
                    {
                        "error": "Failed to parse structured question paper. Try again.",
                        "details": raw_text[:400],
                    }
                ),
                500,
            )

        if output == "text":
            rendered = render_qp_text(qp, part_a_count, part_b_count, part_c_count)
            return jsonify({"question_paper": rendered})

        docx_bytes = build_question_paper_docx(header, qp, part_a_count, part_b_count, part_c_count)
        safe_course = (course_name or "question_paper").replace(" ", "_").replace("/", "_")
        filename = f"question_paper_{safe_course}_{datetime.now().strftime('%Y%m%d')}.docx"

        if output == "google_doc":
            if "credentials" not in session:
                return jsonify({"error": "Not authenticated with Google. Please sign in again to grant Drive access."}), 401
            drive = get_drive_service()
            if not drive:
                return jsonify({"error": "Google Drive service unavailable."}), 500
            docx_bytes.seek(0)
            media = MediaIoBaseUpload(
                docx_bytes,
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                resumable=False,
            )
            file_metadata = {
                "name": filename.replace(".docx", ""),
                "mimeType": "application/vnd.google-apps.document",
            }
            created = drive.files().create(body=file_metadata, media_body=media, fields="id, webViewLink").execute()
            return jsonify({"doc_url": created.get("webViewLink"), "doc_id": created.get("id")})

        return send_file(
            docx_bytes,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    except Exception as exc:
        current_app.logger.exception("Failed to generate question paper: %s", exc)
        error_msg = str(exc)
        status_code = getattr(exc, "status_code", None) or getattr(exc, "status", None)
        if status_code is None:
            if (
                "Error code: 401" in error_msg
                or "UNAUTHENTICATED" in error_msg
                or "API key" in error_msg
                or "permission" in error_msg.lower()
            ):
                status_code = 401
            elif "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                status_code = 429
        if status_code == 401:
            return (
                jsonify(
                    {
                        "error": "Invalid Gemini API key. Please update your key and try again.",
                        "details": error_msg,
                    }
                ),
                401,
            )
        if status_code == 429 or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
            return (
                jsonify(
                    {
                        "error": "Gemini API quota exhausted. Please check your Google AI Studio billing and quota settings.",
                        "details": error_msg,
                    }
                ),
                429,
            )
        return jsonify({"error": "Failed to generate question paper.", "details": error_msg}), status_code or 500
