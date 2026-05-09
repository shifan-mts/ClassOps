def normalize_api_key(value):
    if not value:
        return None
    cleaned = str(value).strip()
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (
        cleaned.startswith("'") and cleaned.endswith("'")
    ):
        cleaned = cleaned[1:-1].strip()
    cleaned = cleaned.strip()
    return cleaned if cleaned else None
