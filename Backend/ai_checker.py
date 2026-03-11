import os
import tempfile
import re
import math
from typing import List, Dict
from collections import Counter
import numpy as np
from langchain_community.document_loaders import PyPDFLoader, UnstructuredFileLoader, Docx2txtLoader

# ==========================================
# 1. AI DETECTION ENGINE (Entropy & Burstiness)
# ==========================================

class AIDetector:
    def __init__(self, text):
        self.text = text
        # Clean text for analysis
        self.clean_text = re.sub(r'\s+', ' ', text).strip()
        self.sentences = [s.strip() for s in re.split(r'[.!?]+', self.clean_text) if len(s.strip()) > 2]
        self.words = re.findall(r'\b\w+\b', self.clean_text.lower())

    def _get_entropy(self):
        """Calculates Shannon Entropy of the word frequency distribution."""
        if not self.words:
            return 0
        counts = Counter(self.words)
        probs = [count / len(self.words) for count in counts.values()]
        return -sum(p * math.log2(p) for p in probs)

    def _get_burstiness(self):
        """Calculates Burstiness (Standard Deviation of sentence lengths)."""
        if len(self.sentences) < 2:
            return 0
        sentence_lengths = [len(s.split()) for s in self.sentences]
        return np.std(sentence_lengths)

    def calculate_score(self):
        """
        Returns AI probability percentage (0-100).
        Lower Entropy (< 3.5) and Lower Burstiness (< 5) suggest AI.
        """
        if not self.words or len(self.words) < 10:
            return 0.0

        entropy = self._get_entropy()
        burstiness = self._get_burstiness()

        # 1. Entropy Score (Threshold based on standard AI predictability)
        # AI texts typically have lower entropy (more predictable word usage)
        e_score = 1 if entropy < 4.0 else 0 
        
        # 2. Burstiness Score (Threshold based on sentence uniformity)
        # AI texts typically have very uniform sentence lengths (low SD)
        b_score = 1 if burstiness < 4.5 else 0
        
        # Weighted Probability (0.6*Entropy + 0.4*Burstiness)
        # We scale it to 100%
        ai_prob = (0.6 * e_score + 0.4 * b_score) * 100
        
        # Add a subtle "shading" based on raw values for more realistic results
        if ai_prob > 0:
            # Slightly adjust based on how far below threshold they are
            adjustment = (4.0 - entropy) * 5 if entropy < 4.0 else 0
            ai_prob = min(99.0, ai_prob + adjustment)

        return round(ai_prob, 2)

# ==========================================
# 2. TEXT NORMALIZATION
# ==========================================

def clean_text_strict(text: str) -> str:
    """Normalizes text for 100% match comparison."""
    if not text or not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ==========================================
# 3. PLAGIARISM DETECTION (Strict 100% Rule)
# ==========================================

def check_strict_plagiarism(submissions: List[Dict]) -> List[Dict]:
    results = []
    for i, sub in enumerate(submissions):
        content = sub.get('clean_content', '')
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
        for j, other_sub in enumerate(submissions):
            if i != j:
                if content == other_sub.get('clean_content', ''):
                    is_copied = True
                    matched_peer = other_sub['name']
                    break

        if is_copied:
            results.append({
                "name": sub['name'],
                "status": "❌ Plagiarized (100% Match)",
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

def detect_ai_content(text: str) -> float:
    """Entry point for single text AI detection."""
    detector = AIDetector(text)
    return detector.calculate_score() / 100.0 # Return 0-1 range for internal app compatibility

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
    except Exception:
        return ""

def analyze_text(text: str) -> Dict:
    if not text or len(text.strip()) == 0:
        return {"success": False, "error": "No text provided"}
    
    score_0_1 = detect_ai_content(text)
    ai_score_percent = score_0_1 * 100
    
    status = "✅ Likely Human"
    if ai_score_percent >= 70: status = "⚠️ Likely AI"
    elif ai_score_percent >= 40: status = "🔶 Partial AI"
        
    return {
        "success": True,
        "ai_score": round(ai_score_percent, 2),
        "status": status,
        "is_ai": ai_score_percent >= 70
    }

def handle_upload(file) -> Dict:
    ext = os.path.splitext(file.filename)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    try:
        content = extract_text_from_file(tmp_path, ext)
        if not content: return {"success": False, "error": "Could not extract text."}
        return analyze_text(content)
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)

def run_batch_analysis(submissions: List[Dict]) -> Dict:
    ai_results = []
    # 1. Clean texts
    for sub in submissions:
        sub['clean_content'] = clean_text_strict(sub.get('content', ''))

    # 2. Run AI Detection using Entropy/Burstiness
    for sub in submissions:
        raw_content = sub.get('content', '')
        if not sub['clean_content'] or len(sub['clean_content'].split()) < 5:
            ai_results.append({"name": sub['name'], "ai_score": 0.0, "status": "⚪ No File Submitted / Empty"})
            continue

        detector = AIDetector(raw_content)
        ai_score = detector.calculate_score()
        
        status = "✅ Likely Human"
        if ai_score >= 70: status = "⚠️ Likely AI"
        elif ai_score >= 40: status = "🔶 Partial AI"
            
        ai_results.append({
            "name": sub['name'],
            "ai_score": round(ai_score, 2),
            "status": status
        })

    # 3. Run Strict Plagiarism Check
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
