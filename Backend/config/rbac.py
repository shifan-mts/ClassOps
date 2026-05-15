DEFAULT_PERMISSIONS = {
    "admin": {
        "overview": ["access", "view", "edit", "manage"],
        "attendance": ["access", "view", "edit", "manage"],
        "meet": ["access", "view", "edit", "manage"],
        "ai-tools": ["access", "view", "edit", "manage"],
        "evaluation": ["access", "view", "edit", "manage"],
        "admin_settings": ["access", "view", "edit", "manage"],
        "dashboard": ["access", "view"],
    },
    "teacher": {
        "overview": ["access", "view", "edit"],
        "attendance": ["access", "view", "edit"],
        "meet": ["access", "view", "edit"],
        "ai-tools": ["access", "view", "edit"],
        "evaluation": ["access", "view", "edit"],
        "admin_settings": [],
        "dashboard": ["access", "view"],
    },
    "student": {
        "overview": ["access", "view"],
        "attendance": ["access", "view"],
        "meet": ["access", "view"],
        "ai-tools": ["access", "view"],
        "evaluation": ["access", "view"],
        "admin_settings": [],
        "dashboard": ["access", "view"],
    },
    "visitor": {
        "overview": [],
        "attendance": [],
        "meet": [],
        "ai-tools": [],
        "evaluation": [],
        "admin_settings": [],
        "dashboard": ["access", "view"],
    }
}

def get_role_permissions(role_name):
    return DEFAULT_PERMISSIONS.get(role_name, DEFAULT_PERMISSIONS["visitor"])
