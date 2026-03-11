import os
import tempfile
import re
import zlib
import math
from typing import List, Dict
from langchain_community.document_loaders import PyPDFLoader, UnstructuredFileLoader, Docx2txtLoader

# Optimal Machine Learning Imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# ==========================================
# 0. AI DETECTION ML SETUP (Modernized)
# ==========================================
# We use a model specifically trained on ChatGPT / Modern LLMs.
# Standard Roberta fails on modern AI. This model provides near state-of-the-art local accuracy.
try:
    from transformers import pipeline
    # Using 'Hello-SimpleAI/chatgpt-detector-roberta' - Highly accurate for modern LLM detection
    ai_detector = pipeline(
        "text-classification", 
        model="Hello-SimpleAI/chatgpt-detector-roberta",
        truncation=True, 
        max_length=512 # Prevents crashing on long documents
    )
    USE_ML_AI_DETECTION = True
except Exception as e:
    print(f"Warning: ML model failed to load. Using fallback heuristics. Error: {e}")
    USE_ML_AI_DETECTION = False

# ==========================================
# 1. TEXT PREPROCESSING
# ==========================================

def clean_text_for_analysis(text: str) -> str:
    """
    Cleans extracted text to prevent false plagiarism matches 
    caused by headers, footers, or bibliography templates.
    """
    if not text or not isinstance(text, str):
        return ""
    text = text.lower()
    # Remove common academic boilerplate
    text = re.sub(r'(references|bibliography|works cited|appendix).*', '', text, flags=re.DOTALL)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove non-alphanumeric chars (keep basic punctuation for AI burstiness checks)
    text = re.sub(r'[^\w\s\.,;?!]', '', text)
    return text.strip()

# ==========================================
# 2. AI DETECTION LOGIC
# ==========================================

def detect_ai_content(text: str) -> float:
    """
    Returns a probability score (0.0 to 1.0) of the text being AI-generated.
    1.0 = 100% AI, 0.0 = 100% Human.
    """
    if not text or len(text.split()) < 20:
        return 0.0 # Too short to reliably tell

    if USE_ML_AI_DETECTION:
        try:
            # The pipeline automatically handles truncation up to 512 tokens.
            result = ai_detector(text)[0]
            # This specific model returns labels 'ChatGPT' or 'Human'
            if result['label'].lower() == 'chatgpt':
                return result['score']
            else:
                return 1.0 - result['score']
        except Exception as e:
            print(f"ML Detection Error: {e}. Falling back to heuristic.")
            pass 
            
    # --- FALLBACK HEURISTIC ---
    # Calculates text predictability and sentence variation
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
        burstiness_score = max(0, 1.0 - (std_dev / 12.0)) # Tighter threshold for AI uniformity
    else:
        burstiness_score = 0.8 # Assume high AI likelihood if structure is weird

    # Predictable text (low ratio) + Uniform sentences (high burst score) = AI
    score = ((1.0 - ratio) * 0.5) + (burstiness_score * 0.5)
    return min(max(score, 0), 1)

# ==========================================
# 3. PLAGIARISM DETECTION (Collusion Check)
# ==========================================

def check_batch_plagiarism(submissions: List[Dict], threshold: float = 0.35) -> List[Dict]:
    """
    Checks if students copied from each other.
    Explicitly handles missing/empty submissions.
    """
    results = []
    valid_subs = []
    
    # 1. Separate valid texts from empty/missing ones
    for sub in submissions:
        content = sub.get('clean_content', '')
        if not content or len(content.split()) < 10:
            results.append({
                "name": sub['name'],
                "status": "⚪ No File Submitted / Empty",
                "highest_match_percent": 0.0,
                "matched_with": "N/A"
            })
        else:
            valid_subs.append(sub)
            
    if len(valid_subs) < 2:
        # Not enough valid files to compare against each other
        for sub in valid_subs:
            results.append({
                "name": sub['name'], 
                "status": "✅ Clean", 
                "highest_match_percent": 0.0, 
                "matched_with": "N/A"
            })
        return results

    texts = [sub['clean_content'] for sub in valid_subs]
    names = [sub['name'] for sub in valid_subs]

    # 2. Build TF-IDF Matrix (Uses 3-word phrases to catch copying)
    try:
        vectorizer = TfidfVectorizer(ngram_range=(3, 3), stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(texts)
        similarity_matrix = cosine_similarity(tfidf_matrix)
    except Exception:
        # Fallback to single words if documents are too short for 3-grams
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(texts)
        similarity_matrix = cosine_similarity(tfidf_matrix)

    # 3. Calculate similarities
    for i in range(len(valid_subs)):
        max_sim = 0.0
        matched_peer = None
        
        for j in range(len(valid_subs)):
            if i != j: # Don't compare a document to itself
                sim_score = similarity_matrix[i][j]
                if sim_score > max_sim:
                    max_sim = sim_score
                    matched_peer = names[j]

        is_copied = max_sim >= threshold
        results.append({
            "name": names[i],
            "status": "❌ Copied/Collusion" if is_copied else "✅ Clean",
            "highest_match_percent": round(max_sim * 100, 2),
            "matched_with": matched_peer if is_copied else "N/A"
        })
        
    # Sort results to match original submission order
    order_map = {sub['name']: index for index, sub in enumerate(submissions)}
    results.sort(key=lambda x: order_map[x['name']])
    
    return results

# ==========================================
# 4. MASTER BATCH EXTRACTION & ANALYSIS
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

def run_batch_analysis(submissions: List[Dict]) -> Dict:
    """
    Main function to analyze a class of submissions.
    Expected Input format:
    [
        {'name': 'Student_1.pdf', 'content': 'Raw text here...'},
        {'name': 'Student_2.pdf', 'content': 'Raw text here...'},
        {'name': 'Student_3.pdf', 'content': ''} # Missing submission
    ]
    """
    ai_results = []
    
    # 1. Preprocess texts
    for sub in submissions:
        sub['clean_content'] = clean_text_for_analysis(sub.get('content', ''))

    # 2. AI Detection
    for sub in submissions:
        if not sub['clean_content'] or len(sub['clean_content'].split()) < 10:
            ai_results.append({
                "name": sub['name'], 
                "ai_score": 0.0, 
                "status": "⚪ No File Submitted / Empty"
            })
            continue

        ai_score = detect_ai_content(sub['clean_content'])
        
        # Stricter grading metrics for AI
        if ai_score >= 0.75:
            ai_status = "⚠️ Highly Likely AI"
        elif ai_score >= 0.40:
            ai_status = "🔶 Partial AI / Edited"
        else:
            ai_status = "✅ Likely Human"
            
        ai_results.append({
            "name": sub['name'],
            "ai_score": round(ai_score * 100, 2),
            "status": ai_status
        })

    # 3. Plagiarism Detection
    plagiarism_results = check_batch_plagiarism(submissions)

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