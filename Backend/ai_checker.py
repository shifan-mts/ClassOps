import os
import tempfile
import requests
from langsmith import traceable
from langchain_community.document_loaders import PyPDFLoader, UnstructuredFileLoader

API_KEY = os.getenv("RAPIDAPI_KEY", "c22f916d7emsh84b9036bb10a1b9p1f1cecjsne5deda81b82a")
API_HOST = os.getenv("RAPIDAPI_HOST", "ai-content-identifier2.p.rapidapi.com")

os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "AiChecker")
os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
os.environ.setdefault("LANGCHAIN_API_KEY", "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")

@traceable
def text_check(user_input):
    """Send the extracted text to an external API for AI content detection."""
    url = f"https://{API_HOST}/text"
    payload = {"text": user_input, "threshold": 10}
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        return {"success": False, "error": str(exc)}


def extract_text(file_path, file_type):
    """Extract text from the uploaded file using appropriate loaders."""
    if file_type == ".pdf":
        loader = PyPDFLoader(file_path)
        document = loader.load()
        return " ".join([page.page_content for page in document])
    if file_type == ".docx":
        loader = UnstructuredFileLoader(file_path)
        document = loader.load()
        return " ".join([page.page_content for page in document])
    return "Unsupported file type"


def _process_path(file_path):
    file_type = os.path.splitext(file_path)[1].lower()
    text_content = extract_text(file_path, file_type)
    result = text_check(text_content)
    return format_response(result, text_content)


@traceable
def handle_upload(file, filename=None):
    """Handle file upload from Flask or a raw path/bytes input."""
    if isinstance(file, str):
        return _process_path(file)

    if isinstance(file, (bytes, bytearray)):
        file_bytes = file
        file_name = filename or "upload"
    else:
        file_bytes = file.read()
        file_name = getattr(file, "filename", None) or filename or "upload"

    file_type = os.path.splitext(file_name)[1].lower()
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_type) as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name
        return _process_path(temp_file_path)
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def format_response(api_response, input_text):
    """Format the API response into structured text, including the original input text."""
    if not api_response:
        return {"success": False, "message": "No response from AI detector."}

    if api_response.get("success") is False and "data" not in api_response:
        return {
            "success": False,
            "message": "Failed to analyze text. Please try again.",
            "error": api_response.get("error")
        }

    data = api_response.get("data", api_response)
    highlighted_text = "; ".join(data.get("highlighted", []))
    stats = data.get("stats", {})

    formatted = (
        f"Original Input Text: {input_text}\n"
        f"AI Content Detected: {data.get('ai', 'Unknown')}\n"
        f"Percentage Ai: {data.get('percentage', 'Unknown')}%\n"
        f"Total Words: {stats.get('totalWords', 'Unknown')}\n"
        f"AI Words: {stats.get('aiWords', 'Unknown')}\n"
        f"Human Words: {stats.get('humanWords', 'Unknown')}\n"
        f"Highlighted Text: {highlighted_text}\n"
    )

    return {
        "success": True,
        "formatted": formatted,
        "data": data
    }


def analyze_text(text):
    result = text_check(text)
    return format_response(result, text)
