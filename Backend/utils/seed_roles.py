from repositories import dynamodb_repository as db
from config.rbac import ROLES_PERMISSIONS

def seed_default_roles():
    """
    Seeds the default roles into DynamoDB if they don't already exist.
    Also seeds the initial admin and demo user role assignments.
    """
    # Seed roles
    for role_name, permissions in ROLES_PERMISSIONS.items():
        # For admin, ensure they have access to admin_settings
        if role_name == "admin":
            permissions["admin_settings"] = ["access", "view", "edit", "modify"]
        
        db.put_role({
            "name": role_name,
            "permissions": permissions
        })
        print(f"Ensured role: {role_name}")

    # Seed initial assignments
    admin_email = "bharatmannar@gmail.com"
    if not db.get_user_role(admin_email):
        db.put_user_role(admin_email, "admin")
        print(f"Seeded admin assignment for {admin_email}")

    demo_email = "bharathmcse2023@jerusalemengg.ac.in"
    if not db.get_user_role(demo_email):
        db.put_user_role(demo_email, "demo")
        print(f"Seeded demo assignment for {demo_email}")
