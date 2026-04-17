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
    
    if not email.endswith("@jerusalemengg.ac.in"):
        return result
        
    local_part = email.split('@')[0].lower()
    
    # Check if local part is entirely alphabetic (Teacher)
    if re.fullmatch(r'[a-z]+', local_part):
        result["role"] = "teacher"
        return result
        
    # Standard list of likely departments based on typical engineering colleges
    known_depts = ["cse", "ece", "eee", "it", "mech", "civil", "bme", "aids", "csbs", "ai", "ds", "mba", "mca"]
    dept_pattern = '|'.join(sorted(known_depts, key=len, reverse=True))
    
    # Regex: (any letters for name) + (known department) + (4 digits for year)
    student_pattern = r'^[a-z]+?(' + dept_pattern + r')(\d{4})$'
    match = re.search(student_pattern, local_part)
    
    if match:
        dept = match.group(1)
        batch = int(match.group(2))
        grade_year = current_year - batch
        
        result["role"] = "student"
        result["dept"] = dept.upper()
        result["batch"] = batch
        result["current_year"] = grade_year if grade_year > 0 else None
        
    return result
