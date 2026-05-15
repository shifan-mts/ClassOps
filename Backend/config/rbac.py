# config/rbac.py

ROLES_PERMISSIONS = {
    "admin": {
        "overview": ["access", "view", "edit", "modify"],
        "attendance": ["access", "view", "edit", "modify"],
        "meet": ["access", "view", "edit", "modify"],
        "ai-tools": ["access", "view", "edit", "modify"],
        "evaluations": ["access", "view", "edit", "modify"],
        "timetable": ["access", "view", "edit", "modify"],
        "dashboard": ["access", "view", "edit", "modify"],
        "admin_settings": ["access", "view", "edit", "modify"],
    },
    "teacher": {
        "overview": ["access", "view", "edit", "modify"],
        "attendance": ["access", "view", "edit", "modify"],
        "meet": ["access", "view", "edit", "modify"],
        "ai-tools": ["access", "view", "edit", "modify"],
        "evaluations": ["access", "view", "edit", "modify"],
        "timetable": ["access", "view", "edit", "modify"],
        "dashboard": ["access", "view"],
    },
    "demo": {
        "overview": ["access", "view"],
        "attendance": ["access", "view"],
        "meet": ["access", "view"],
        "ai-tools": ["access", "view", "edit"],  # Allow demoing AI generation
        "evaluations": ["access", "view"],
        "timetable": ["access", "view"],
        "dashboard": ["access", "view"],
    },
    "student": {
        "overview": [],
        "attendance": [],
        "meet": [],
        "ai-tools": [],
        "evaluations": [],
        "timetable": [],
        "dashboard": ["access", "view"],
    }
}

def get_role_permissions(role: str) -> dict:
    """Returns the permissions dictionary for a given role, or empty dict if role is unknown."""
    return ROLES_PERMISSIONS.get(role, {})
