import re

def parse_jerusalem_email(email: str, current_year: int = 2026):
    """
    Parses a Jerusalem Engineering College email to identify the user's role and details.
    Returns a dict with email, role, dept, batch, and current_year.
    """
    result = {
        "email": email,
        "role": "unknown",
        "dept": None,
        "batch": None,
        "current_year": None
    }
    
    # Teacher bypass list
    teacher_whitelist = [
        "amohamedshifan1@gmail.com",
        "bharadwajvaradan2005@gmail.com",
        "bharatmannar@gmail.com" # Also in admin, but admin catches it first
    ]
    if email.lower() in teacher_whitelist:
        result["role"] = "teacher"
        return result
    
    # Allow common typo for the domain
    if not email.endswith("@jerusalemengg.ac.in"):
        return result
        
    # Check if the email local part ends with a 4-digit year (student pattern)
    local_part = email.split('@')[0].lower()
    
    # Check for 4 digits at the end of the local part (e.g., name2023, name-dept2024)
    match = re.search(r'(\d{4})$', local_part)
    
    if match:
        batch = int(match.group(1))
        # Optional: Try to extract department if it precedes the year
        # e.g., 'shifan-it2023' -> 'IT'
        known_depts = ["cse", "ece", "eee", "it", "mech", "civil", "bme", "aids", "csbs", "ai", "ds", "mba", "mca"]
        dept_match = re.search(r'(' + '|'.join(known_depts) + r')', local_part)
        
        result["role"] = "student"
        result["dept"] = dept_match.group(1).upper() if dept_match else "UNKNOWN"
        result["batch"] = batch
        result["current_year"] = current_year - batch if (current_year - batch) > 0 else None
    else:
        # If it's from the college domain but doesn't have a year at the end, it's a teacher
        result["role"] = "teacher"
        
    return result
