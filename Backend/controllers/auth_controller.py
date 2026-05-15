import base64
import json
import os

from flask import current_app, jsonify, redirect, request, session
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from config.constants import CLIENT_SECRETS_FILE, SCOPES
from email_parser import parse_jerusalem_email
from repositories import dynamodb_repository as db
from services.google_service import (
    build_credentials_payload,
    get_redirect_uri,
    sync_classroom_data,
)
from services.teacher_service import get_authenticated_teacher
from config.rbac import get_role_permissions


def _load_google_client_config_from_env():
    raw_config = os.getenv("GOOGLE_CLIENT_SECRETS_JSON")
    raw_config_b64 = os.getenv("GOOGLE_CLIENT_SECRETS_B64")
    if raw_config_b64 and not raw_config:
        raw_config = base64.b64decode(raw_config_b64).decode("utf-8")
    if raw_config:
        return json.loads(raw_config)

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if client_id and client_secret:
        return {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [os.getenv("REDIRECT_URI")] if os.getenv("REDIRECT_URI") else [],
            }
        }

    return None


def _create_oauth_flow(state=None):
    client_config = _load_google_client_config_from_env()
    if client_config:
        return Flow.from_client_config(client_config, scopes=SCOPES, state=state)
    return Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)


def google_auth():
    flow = _create_oauth_flow()
    flow.redirect_uri = get_redirect_uri()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="select_account consent",
    )
    session["state"] = state
    session["code_verifier"] = flow.code_verifier
    session.modified = True
    return redirect(authorization_url)


def google_auth_url():
    flow = _create_oauth_flow()
    flow.redirect_uri = get_redirect_uri()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="select_account consent",
    )
    session["state"] = state
    session["code_verifier"] = flow.code_verifier
    session.modified = True
    return jsonify({"auth_url": authorization_url})


def google_auth_callback():
    state = session.get("state")
    code_verifier = session.get("code_verifier")

    if not state:
        current_app.logger.error("No state found in session")
        return jsonify({"error": "Missing OAuth state. Please enable cookies and try again."}), 400
    
    if not code_verifier:
        current_app.logger.error("No code_verifier found in session")
        return jsonify({"error": "Missing OAuth code verifier. Please try again."}), 400

    try:
        url_state = request.args.get("state")
        flow = _create_oauth_flow(state=url_state or state)
        flow.redirect_uri = get_redirect_uri()

        # Build authorization response URL accurately
        authorization_response = request.url
        base = os.getenv("BASE_URL", request.host_url.rstrip("/"))
        if "onrender.com" in base:
            authorization_response = authorization_response.replace("http://", "https://")
        elif "localhost" in base and "127.0.0.1" in authorization_response:
            authorization_response = authorization_response.replace("127.0.0.1", "localhost")

        flow.fetch_token(authorization_response=authorization_response, code_verifier=code_verifier)

        credentials = flow.credentials
        
        # Get user info BEFORE setting session data
        user_info_service = build("oauth2", "v2", credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        email = user_info.get("email")
        name = user_info.get("name", "Unknown User")
        
        # Verify role before committing to the session
        parsed = parse_jerusalem_email(email)
        if email == "angelinehephzibahj@gmail.com":
            parsed["role"] = "teacher"

        # Check DB for explicit role assignment
        explicit_role = db.get_user_role(email)
        if explicit_role:
            parsed["role"] = explicit_role["role"]

        if parsed["role"] == "unknown":
            # Fallback to visitor instead of denying access
            parsed["role"] = "visitor"
            current_app.logger.info(f"Unauthorized email {email} assigned visitor role.")

        # Fetch permissions from DB, fallback to static config
        role_record = db.get_role(parsed["role"])
        permissions = role_record.get("permissions", {}) if role_record else get_role_permissions(parsed["role"])

        # Prepare user object
        user_data = {
            "id": user_info.get("id"),
            "email": email,
            "name": name,
            "picture": user_info.get("picture"),
            "role": parsed["role"],
            "permissions": permissions
        }

        if parsed["role"] == "student":
            user_data["dept"] = parsed.get("dept")
            user_data["batch"] = parsed.get("batch")
            user_data["current_year"] = parsed.get("current_year")

        # COMMIT to session only after full validation
        session["user"] = user_data
        session["credentials"] = build_credentials_payload(credentials)
        session.modified = True

        # Frontend redirect URL
        if "onrender.com" in base:
            frontend_url = base
        else:
            frontend_url = "http://localhost:5173"

        # Perform teacher-specific initialization
        if parsed["role"] == "teacher":
            teacher = db.get_teacher(email)
            if not teacher:
                teacher = {
                    "email": email,
                    "name": name,
                    "availability": {},
                    "period_timings": {},
                }
                db.put_teacher(teacher)
            
            try:
                sync_classroom_data(session["credentials"])
            except Exception as exc:
                current_app.logger.exception("Classroom sync failed: %s", exc)

        return redirect(f"{frontend_url}/")

    except Exception as exc:
        current_app.logger.exception("OAuth callback error: %s", exc)
        session.clear()
        return jsonify({"error": str(exc)}), 500


def get_me():
    if "user" not in session:
        return jsonify({"authenticated": False}), 401

    user_data = session["user"]
    role_name = user_data.get("role")
    
    # Refresh permissions from DB to reflect any recent changes
    if role_name:
        role_record = db.get_role(role_name)
        if role_record:
            user_data["permissions"] = role_record.get("permissions", {})
            session["user"] = user_data
            session.modified = True

    return jsonify({"authenticated": True, "user": user_data})


def logout():
    session.clear()
    response = jsonify({"message": "Logged out successfully"})
    response.delete_cookie("session")
    return response, 200


def sync_classroom():
    if "credentials" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    sync_classroom_data(session["credentials"])
    teacher = get_authenticated_teacher()
    if not teacher:
        return jsonify({"error": "Unauthorized"}), 401

    courses = db.get_courses_by_teacher(teacher["email"])
    return jsonify(
        {
            "message": "Classroom synced successfully",
            "courses": [
                {
                    "id": course.get("id"),
                    "google_course_id": course.get("google_course_id"),
                    "name": course.get("name"),
                }
                for course in courses
            ],
        }
    )
