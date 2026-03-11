import os
import tempfile
import re
import zlib
import math
from typing import List, Dict
from langchain_community.document_loaders import PyPDFLoader, UnstructuredFileLoader, Docx2txtLoader

# Optimal Machine Learning Imports
import numpy as np

# ==========================================
# 0. AI DETECTION ML SETUP
# ==========================================
try:
    from transformers import pipeline
    # High-accuracy model for detecting ChatGPT/LLM content
    ai_detector = pipeline(
        "text-classification", 
        model="Hello-SimpleAI/chatgpt-detector-roberta",
        truncation=True, 
        max_length=512
    )
    USE_ML_AI_DETECTION = True
except Exception as e:
    print(f"Warning: ML model failed to load. Using fallback heuristics. Error: {e}")
    USE_ML_AI_DETECTION = False

# ==========================================
# 1. TEXT PREPROCESSING
# ==========================================

def clean_text_strict(text: str) -> str:
    """
    Normalizes text for a STRICT 100% match comparison.
    Removes extra spaces, makes everything lowercase, and strips punctuation.
    """
    if not text or not isinstance(text, str):
        return ""
    
    text = text.lower()
    # Remove all punctuation and symbols to get just the raw words
    text = re.sub(r'[^\w\s]', '', text)
    # Replace multiple spaces/newlines with a single space
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

# ==========================================
# 2. AI DETECTION LOGIC
# ==========================================

def detect_ai_content(text: str) -> float:
    if not text or len(text.split()) < 20:
        return 0.0

    if USE_ML_AI_DETECTION:
        try:
            result = ai_detector(text)[0]
            if result['label'].lower() == 'chatgpt':
                return result['score']
            else:
                return 1.0 - result['score']
        except Exception:
            pass 
            
    # --- FALLBACK HEURISTIC ---
    try:
        compressed = zlib.compress(text.encode('utf-8'))
        ratio = len(compressed) / len(text)
    except:
        ratio = 0.5

    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 5]
    if len(sentences) > 2:
        lens = [len(s.split()) for s in sentences]
        mean = sum(lens) / len(lens)
        std_dev = math.sqrt(sum((x - mean) ** 2 for x in lens) / len(lens))
        burstiness_score = max(0, 1.0 - (std_dev / 12.0))
    else:
        burstiness_score = 0.8

    score = ((1.0 - ratio) * 0.5) + (burstiness_score * 0.5)
    return min(max(score, 0), 1)

# ==========================================
# 3. PLAGIARISM DETECTION (Strict 100% Rule)
# ==========================================

def check_strict_plagiarism(submissions: List[Dict]) -> List[Dict]:
    """
    Checks if students copied from each other.
    Flags ONLY if the normalized content is a 100% exact match.
    """
    results = []
    
    for i, sub in enumerate(submissions):
        content = sub.get('clean_content', '')
        
        # 1. Handle Empty Files explicitly
        if not content or len(content.split()) < 5:
            results.append({
                "name": sub['name'],
                "status": "⚪ No File Submitted / Empty",
                "highest_match_percent": 0.0,
                "matched_with": "N/A"
            })
            continue
            
        is_copied = False
        matched_peer = None
        
        # 2. Compare against all others for a 100% match
        for j, other_sub in enumerate(submissions):
            if i != j:
                other_content = other_sub.get('clean_content', '')
                
                # STRICT 100% EQUALITY CHECK
                if content == other_content and len(other_content) > 0:
                    is_copied = True
                    matched_peer = other_sub['name']
                    break

        if is_copied:
            results.append({
                "name": sub['name'],
                "status": "❌ Plagiarized (100% Exact Match)",
                "highest_match_percent": 100.0,
                "matched_with": matched_peer
            })
        else:
            results.append({
                "name": sub['name'],
                "status": "✅ Unique",
                "highest_match_percent": 0.0,
                "matched_with": "N/A"
            })
            
    return results

# ==========================================
# 4. EXPORTED API UTILITIES
# ==========================================

def extract_text_from_file(file_path: str, ext: str) -> str:
    try:
        if ext == '.pdf':
            loader = PyPDFLoader(file_path)
            return " ".join([p.page_content for p in loader.load()])
        elif ext in ['.docx', '.doc']:
            loader = Docx2txtLoader(file_path)
            return loader.load()[0].page_content
        else:
            loader = UnstructuredFileLoader(file_path)
            return loader.load()[0].page_content
    except Exception as e:
        print(f"Failed to extract {file_path}: {e}")
        return ""

def analyze_text(text: str) -> Dict:
    if not text or len(text.strip()) == 0:
        return {"success": False, "error": "No text provided"}
    
    clean_text = clean_text_strict(text)
    ai_score = detect_ai_content(text)
    
    status = "✅ Likely Human"
    if ai_score >= 0.75: status = "⚠️ Highly Likely AI"
    elif ai_score >= 0.40: status = "🔶 Partial AI / Edited"
        
    return {
        "success": True,
        "ai_score": round(ai_score * 100, 2),
        "status": status,
        "is_ai": ai_score >= 0.75
    }

def handle_upload(file) -> Dict:
    ext = os.path.splitext(file.filename)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    try:
        content = extract_text_from_file(tmp_path, ext)
        if not content:
            return {"success": False, "error": "Could not extract text from file."}
        return analyze_text(content)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def run_batch_analysis(submissions: List[Dict]) -> Dict:
    ai_results = []
    
    # 1. Clean texts for strict 100% matching
    for sub in submissions:
        sub['clean_content'] = clean_text_strict(sub.get('content', ''))

    # 2. Run AI Detection
    for sub in submissions:
        raw_content = sub.get('content', '')
        
        if not sub['clean_content'] or len(sub['clean_content'].split()) < 5:
            ai_results.append({
                "name": sub['name'], 
                "ai_score": 0.0, 
                "status": "⚪ No File Submitted / Empty"
            })
            continue

        ai_score = detect_ai_content(raw_content)
        ai_status = "✅ Likely Human"
        if ai_score >= 0.75: ai_status = "⚠️ Highly Likely AI"
        elif ai_score >= 0.40: ai_status = "🔶 Partial AI / Edited"
            
        ai_results.append({
            "name": sub['name'],
            "ai_score": round(ai_score * 100, 2),
            "status": ai_status
        })

    # 3. Run STRICT 100% Plagiarism Detection
    plagiarism_results = check_strict_plagiarism(submissions)

    return {
        "summary": {
            "total_processed": len(submissions),
            "missing_submissions": sum(1 for r in ai_results if "⚪" in r['status']),
            "ai_detected": sum(1 for r in ai_results if "⚠️" in r['status']),
            "plagiarism_detected": sum(1 for r in plagiarism_results if "❌" in r['status'])
        },
        "ai_results": ai_results,
        "plagiarism_results": plagiarism_results
    }
