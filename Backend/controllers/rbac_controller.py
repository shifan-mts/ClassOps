from flask import jsonify, request
from repositories import dynamodb_repository as db

def get_roles():
    roles = db.scan_all_roles()
    return jsonify(roles)

def create_role():
    data = request.json
    if not data or not data.get("name"):
        return jsonify({"error": "Role name is required"}), 400
    if "permissions" not in data:
        data["permissions"] = {}
    
    role = db.put_role(data)
    return jsonify(role), 201

def update_role(role_name):
    data = request.json
    if not data:
        return jsonify({"error": "Data is required"}), 400
    
    data["name"] = role_name
    if "permissions" not in data:
        data["permissions"] = {}
        
    role = db.put_role(data)
    return jsonify(role)

def delete_role(role_name):
    if role_name in ["admin", "teacher", "student", "demo"]:
        return jsonify({"error": "Cannot delete default roles"}), 400
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
    
    if not emails or not role_name:
        return jsonify({"error": "Emails and role are required"}), 400
        
    assignments = []
    for email in emails:
        email = email.strip()
        if email:
            assignments.append(db.put_user_role(email, role_name))
            
    return jsonify({"message": "Assignments created successfully", "assignments": assignments}), 201

def delete_role_assignment(email):
    # Prevent deleting the last admin if possible, but for simplicity just delete
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
