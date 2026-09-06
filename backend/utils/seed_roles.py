from repositories import dynamodb_repository as db
from config.rbac import INITIAL_ROLES, INITIAL_COMPONENTS

def seed_default_roles():
    print("Initializing Database RBAC Seeding...")
    
    # 1. Seed Components
    existing_comps = {c["id"] for c in db.scan_all_components()}
    for comp in INITIAL_COMPONENTS:
        if comp["id"] not in existing_comps:
            print(f"Seeding Component: {comp['id']}")
            db.put_component(comp)
        else:
            print(f"Component '{comp['id']}' exists, skipping.")

    # 2. Seed Roles
    existing_roles = {r["name"] for r in db.scan_all_roles()}
    for role_name, permissions in INITIAL_ROLES.items():
        if role_name not in existing_roles:
            print(f"Seeding Role: {role_name}")
            role_data = {
                "name": role_name,
                "permissions": permissions,
                "color": get_default_color(role_name)
            }
            db.put_role(role_data)
        else:
            print(f"Role '{role_name}' exists, skipping.")
            
    print("Database initialization check completed.")

def get_default_color(role_name):
    colors = {
        "admin": "#f04747",
        "teacher": "#faa61a",
        "student": "#3ba55c",
        "visitor": "#747f8d"
    }
    return colors.get(role_name, "#7289da")
