from flask import jsonify, session
from repositories import dynamodb_repository as db
from services.teacher_service import get_authenticated_teacher

def get_dashboard_stats():
    if "user" not in session:
        return jsonify({"error": "Not authenticated"}), 401
        
    user = session["user"]
    role = user.get("role")
    
    stats = {}
    
    if role == "admin":
        all_courses = db.get_all_courses()
        all_roles = db.scan_all_roles()
        all_assignments = db.scan_all_user_roles()
        
        stats = {
            "total_courses": len(all_courses),
            "total_roles": len(all_roles),
            "total_custom_assignments": len(all_assignments)
        }
    elif role == "teacher" or role == "demo":
        teacher = get_authenticated_teacher()
        if teacher:
            courses = db.get_courses_by_teacher(teacher["email"])
            stats = {
                "total_courses": len(courses)
            }
        else:
            stats = {"total_courses": 0}
            
    return jsonify(stats), 200
