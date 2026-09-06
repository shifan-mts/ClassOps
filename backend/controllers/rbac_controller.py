from flask import jsonify, request
from repositories import dynamodb_repository as db
from datetime import datetime, timedelta

def get_roles():
    roles = db.scan_all_roles()
    return jsonify(roles)

def create_role():
    data = request.json
    if not data or not data.get("name"):
        return jsonify({"error": "Role name is required"}), 400
    if "permissions" not in data:
        data["permissions"] = {}
    
    # Department support
    if "department" not in data:
        data["department"] = "Common"
    
    # Custom color support
    if "color" not in data:
        data["color"] = "#7289da" # default blurple
        
    role = db.put_role(data)
    return jsonify(role), 201

def update_role(role_name):
    data = request.json
    if not data:
        return jsonify({"error": "Data is required"}), 400
    
    data["name"] = role_name
    if "permissions" not in data:
        data["permissions"] = {}
    
    if "department" not in data:
        data["department"] = "Common"
        
    role = db.put_role(data)
    return jsonify(role)

def delete_role(role_name):
    if role_name in ["teacher", "student"]:
        return jsonify({"error": "Cannot delete core system roles (teacher/student)"}), 400
    db.delete_role(role_name)
    return jsonify({"message": "Role deleted successfully"})

def get_role_assignments():
    assignments = db.scan_all_user_roles()
    return jsonify(assignments)

def create_role_assignment():
    data = request.json
    emails = data.get("emails", [])
    if "email" in data and data["email"]:
        emails.append(data["email"])
        
    role_name = data.get("role")
    duration_hrs = data.get("duration_hrs") # Optional duration in hours
    
    if not emails or not role_name:
        return jsonify({"error": "Emails and role are required"}), 400
    
    expires_at = None
    if duration_hrs:
        try:
            expires_at = (datetime.now() + timedelta(hours=float(duration_hrs))).isoformat()
        except:
            pass
            
    assignments = []
    for email in emails:
        email = email.strip()
        if email:
            assignments.append(db.put_user_role(email, role_name, expires_at))
            
    return jsonify({"message": "Assignments created successfully", "assignments": assignments}), 201

def delete_role_assignment(email):
    db.delete_user_role(email)
    return jsonify({"message": "Assignment deleted successfully"})

def bulk_delete_role_assignments():
    data = request.json
    emails = data.get("emails", [])
    if not emails:
        return jsonify({"error": "Emails are required"}), 400
        
    for email in emails:
        db.delete_user_role(email)
    return jsonify({"message": "Assignments deleted successfully"})

def bulk_import():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # 1. Import Roles
    roles = data.get("roles", [])
    for role_data in roles:
        if role_data.get("name"):
            # Ensure mandatory fields
            if "permissions" not in role_data:
                role_data["permissions"] = {}
            if "department" not in role_data:
                role_data["department"] = "Common"
            if "color" not in role_data:
                role_data["color"] = "#7289da"
            db.put_role(role_data)
            
    # 2. Import Assignments
    assignments = data.get("assignments", [])
    for assign_data in assignments:
        email = assign_data.get("email")
        role = assign_data.get("role")
        if email and role:
            duration = assign_data.get("duration_hrs")
            expires_at = None
            if duration:
                try:
                    expires_at = (datetime.now() + timedelta(hours=float(duration))).isoformat()
                except:
                    pass
            db.put_user_role(email.strip(), role, expires_at)
            
    return jsonify({"message": f"Bulk import complete. Imported {len(roles)} roles and {len(assignments)} assignments."})
