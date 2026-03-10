import os
import re
import tempfile
import requests
from pypdf import PdfReader
from docx import Document

MAX_CHARS = int(os.getenv("AI_CHECK_MAX_CHARS", "12000"))
MAX_PREVIEW_CHARS = int(os.getenv("AI_CHECK_PREVIEW_CHARS", "1500"))


def _clean_env(value):
    if value is None:
        return None
    return value.strip().strip('"').strip("'")


def _normalize_text(text):
    if not text:
        return ""
    return " ".join(text.split())


def _truncate(text, limit):
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit]


def extract_text(file_path, file_type):
    if file_type == ".pdf":
        reader = PdfReader(file_path)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    if file_type == ".docx":
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs if p.text)
    return ""


def _extract_from_bytes(file_bytes, file_name):
    file_type = os.path.splitext(file_name)[1].lower()
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_type) as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name
        return extract_text(temp_file_path, file_type)
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def extract_text_from_bytes(file_bytes, file_name):
    return _extract_from_bytes(file_bytes, file_name)


def text_check(user_input, api_key=None, api_host=None):
    api_key = _clean_env(api_key or os.getenv("RAPIDAPI_KEY"))
    api_host = _clean_env(api_host or os.getenv("RAPIDAPI_HOST", "ai-content-identifier2.p.rapidapi.com"))
    if not api_key:
        return {"success": False, "error": "Missing RapidAPI key"}

    url = f"https://{api_host}/text"
    payload = {"text": user_input, "threshold": 10}
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": api_host,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        return {"success": False, "error": str(exc)}


def _heuristic_analysis(text):
    words = re.findall(r"[A-Za-z0-9']+", text.lower())
    total_words = len(words)
    if total_words == 0:
        return {
            "ai": "Unknown",
            "percentage": 0,
            "highlighted": [],
            "stats": {"totalWords": 0, "aiWords": 0, "humanWords": 0}
        }

    unique_ratio = len(set(words)) / total_words
    sentence_count = max(1, text.count('.') + text.count('!') + text.count('?'))
    avg_sentence_len = total_words / sentence_count
    avg_word_len = sum(len(w) for w in words) / total_words

    ai_score = (avg_sentence_len / 25.0) * 40.0 + (1.0 - unique_ratio) * 50.0 + (avg_word_len / 6.0) * 10.0
    ai_score = max(0.0, min(100.0, ai_score))

    if ai_score >= 65:
        label = "Likely AI"
    elif ai_score >= 45:
        label = "Mixed"
    else:
        label = "Likely Human"

    return {
        "ai": label,
        "percentage": round(ai_score, 1),
        "highlighted": [],
        "stats": {
            "totalWords": total_words,
            "aiWords": int(total_words * ai_score / 100.0),
            "humanWords": int(total_words - (total_words * ai_score / 100.0))
        }
    }


def format_response(data, input_text, source="rapidapi", note=None):
    input_text = _normalize_text(input_text)
    preview = _truncate(input_text, MAX_PREVIEW_CHARS)
    truncated = len(input_text) > len(preview)

    highlighted_text = "; ".join(data.get("highlighted", []) or [])
    stats = data.get("stats", {})

    formatted = (
        f"Input Preview: {preview}{'...' if truncated else ''}\n"
        f"AI Content Detected: {data.get('ai', 'Unknown')}\n"
        f"AI Percentage: {data.get('percentage', 'Unknown')}%\n"
        f"Total Words: {stats.get('totalWords', 'Unknown')}\n"
        f"AI Words: {stats.get('aiWords', 'Unknown')}\n"
        f"Human Words: {stats.get('humanWords', 'Unknown')}\n"
        f"Highlighted Text: {highlighted_text}\n"
        f"Source: {source}\n"
    )

    if note:
        formatted += f"Note: {note}\n"

    return {
        "success": True,
        "formatted": formatted,
        "data": data,
        "meta": {
            "source": source,
            "text_length": len(input_text),
            "truncated": truncated
        }
    }


def analyze_text(text):
    if not text:
        return {"success": False, "message": "No text provided"}

    cleaned = _truncate(_normalize_text(text), MAX_CHARS)
    api_response = text_check(cleaned)

    if isinstance(api_response, dict) and api_response.get("success") is False and "data" not in api_response:
        data = _heuristic_analysis(cleaned)
        return format_response(data, cleaned, source="heuristic", note="RapidAPI unavailable; using heuristic estimate.")

    data = api_response.get("data", api_response)
    return format_response(data, cleaned, source="rapidapi")


def handle_upload(file, filename=None):
    if isinstance(file, str):
        file_path = file
        file_type = os.path.splitext(file_path)[1].lower()
        text_content = extract_text(file_path, file_type)
    elif isinstance(file, (bytes, bytearray)):
        file_bytes = file
        file_name = filename or "upload"
        text_content = _extract_from_bytes(file_bytes, file_name)
    else:
        file_bytes = file.read()
        file_name = getattr(file, "filename", None) or filename or "upload"
        text_content = _extract_from_bytes(file_bytes, file_name)

    cleaned = _truncate(_normalize_text(text_content), MAX_CHARS)
    api_response = text_check(cleaned)

    if isinstance(api_response, dict) and api_response.get("success") is False and "data" not in api_response:
        data = _heuristic_analysis(cleaned)
        return format_response(data, cleaned, source="heuristic", note="RapidAPI unavailable; using heuristic estimate.")

    data = api_response.get("data", api_response)
    return format_response(data, cleaned, source="rapidapi")
