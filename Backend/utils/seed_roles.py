from repositories import dynamodb_repository as db
from config.rbac import DEFAULT_PERMISSIONS

def seed_default_roles():
    print("Seeding default roles...")
    for role_name, permissions in DEFAULT_PERMISSIONS.items():
        role_data = {
            "name": role_name,
            "permissions": permissions,
            "color": get_default_color(role_name)
        }
        db.put_role(role_data)
    print("Seeding completed.")

def get_default_color(role_name):
    colors = {
        "admin": "#f04747",    # Red
        "teacher": "#7289da",  # Blurple
        "student": "#43b581",  # Green
        "visitor": "#747f8d"   # Grey
    }
    return colors.get(role_name, "#7289da")
