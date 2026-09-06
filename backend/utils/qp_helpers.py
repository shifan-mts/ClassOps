import json
import os
from datetime import datetime
from io import BytesIO


def get_qp_header(data, course_name):
    return {
        "college_name": data.get("college_name") or os.getenv("QP_COLLEGE_NAME", "COLLEGE NAME"),
        "college_address": data.get("college_address") or os.getenv("QP_COLLEGE_ADDRESS", ""),
        "affiliation": data.get("affiliation") or os.getenv("QP_AFFILIATION", ""),
        "academic_year": data.get("academic_year") or os.getenv("QP_ACADEMIC_YEAR", ""),
        "assessment": data.get("assessment") or os.getenv("QP_ASSESSMENT", "Assessment Test - II"),
        "course_code": data.get("course_code") or os.getenv("QP_COURSE_CODE", ""),
        "course_title": data.get("course_title") or course_name,
        "date": data.get("date") or os.getenv("QP_DATE", datetime.now().strftime("%d/%m/%Y")),
        "time": data.get("time") or os.getenv("QP_TIME", ""),
        "max_marks": data.get("max_marks") or os.getenv("QP_MAX_MARKS", ""),
    }


def build_qp_prompt(topic, course_name, difficulty, part_a_count, part_b_count, part_c_count):
    return f"""Generate a university assessment question paper.
Return ONLY a JSON object matching the response schema. No extra text.

Rules:
- Part A: {part_a_count} short questions (2 marks each).
- Part B: {part_b_count} long questions (16 marks each) with OR alternatives.
- Part C: {part_c_count} long questions (8 marks each) with OR alternatives.
- Keep each question under 20 words.
- Use CO1-CO5 and K1-K6.

Topic: {topic}. Course: {course_name}. Difficulty: {difficulty}.
"""


def get_qp_schema(part_a_count, part_b_count, part_c_count):
    part_a_item = {
        "type": "object",
        "required": ["question", "co", "bloom"],
        "properties": {
            "question": {"type": "string"},
            "co": {"type": "string"},
            "bloom": {"type": "string"},
        },
    }
    part_b_item = {
        "type": "object",
        "required": ["question", "co", "bloom", "or_question", "or_co", "or_bloom"],
        "properties": {
            "question": {"type": "string"},
            "co": {"type": "string"},
            "bloom": {"type": "string"},
            "or_question": {"type": "string"},
            "or_co": {"type": "string"},
            "or_bloom": {"type": "string"},
        },
    }
    part_c_item = {
        "type": "object",
        "required": ["question", "co", "bloom", "or_question", "or_co", "or_bloom"],
        "properties": {
            "question": {"type": "string"},
            "co": {"type": "string"},
            "bloom": {"type": "string"},
            "or_question": {"type": "string"},
            "or_co": {"type": "string"},
            "or_bloom": {"type": "string"},
        },
    }
    return {
        "type": "object",
        "required": ["part_a", "part_b", "part_c"],
        "properties": {
            "part_a": {
                "type": "array",
                "items": part_a_item,
                "minItems": part_a_count,
                "maxItems": part_a_count,
            },
            "part_b": {
                "type": "array",
                "items": part_b_item,
                "minItems": part_b_count,
                "maxItems": part_b_count,
            },
            "part_c": {
                "type": "array",
                "items": part_c_item,
                "minItems": part_c_count,
                "maxItems": part_c_count,
            },
        },
    }


def parse_qp_json(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def extract_json_object(text):
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def normalize_qp(qp, part_a_count, part_b_count, part_c_count):
    if not isinstance(qp, dict):
        return None
    part_a = qp.get("part_a") or []
    part_b = qp.get("part_b") or []
    part_c = qp.get("part_c") or []

    if len(part_a) < part_a_count or len(part_b) < part_b_count or len(part_c) < part_c_count:
        return None

    qp["part_a"] = part_a[:part_a_count]
    qp["part_b"] = part_b[:part_b_count]
    qp["part_c"] = part_c[:part_c_count]
    return qp


def render_qp_text(qp, part_a_count, part_b_count, part_c_count):
    lines = []
    part_a = qp.get("part_a", [])
    part_b = qp.get("part_b", [])
    part_c = qp.get("part_c", [])

    lines.append(f"PART - A ({part_a_count} x 2 = {part_a_count * 2} marks)")
    lines.append("Answer all the Questions")
    for idx, q in enumerate(part_a, start=1):
        lines.append(f"{idx}. {q.get('question', '')} (CO: {q.get('co', '')}, {q.get('bloom', '')})")

    lines.append(f"\nPART - B (2 x 16 = 32 marks)")
    for i, q in enumerate(part_b, start=1):
        no = part_a_count + i
        lines.append(f"{no}(a). {q.get('question', '')} (CO: {q.get('co', '')}, {q.get('bloom', '')})")
        lines.append("OR")
        lines.append(f"{no}(b). {q.get('or_question', '')} (CO: {q.get('or_co', '')}, {q.get('or_bloom', '')})")

    lines.append(f"\nPART - C (1 x 8 = 8 marks)")
    for i, q in enumerate(part_c, start=1):
        no = part_a_count + part_b_count + i
        lines.append(f"{no}(a). {q.get('question', '')} (CO: {q.get('co', '')}, {q.get('bloom', '')})")
        lines.append("OR")
        lines.append(f"{no}(b). {q.get('or_question', '')} (CO: {q.get('or_co', '')}, {q.get('or_bloom', '')})")

    return "".join(lines)


def build_question_paper_docx(header, qp, part_a_count, part_b_count, part_c_count):
    try:
        from docx import Document
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
        from docx.shared import Pt
    except ImportError:
        raise Exception("python-docx is not installed. Question paper generation in DOCX format is disabled.")

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(11)

    reg = doc.add_paragraph()
    reg.add_run("Reg.No.: ").bold = True
    reg.add_run("____________________")

    def add_center_line(text, bold=False):
        if not text:
            return
        p = doc.add_paragraph()
        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run = p.add_run(text)
        run.bold = bold

    college_line = header.get("college_name")
    if header.get("college_address"):
        college_line = f"{college_line}, {header.get('college_address')}".strip(", ")
    add_center_line(college_line, bold=True)
    add_center_line(header.get("affiliation"))
    add_center_line(header.get("academic_year"))
    add_center_line(header.get("assessment"), bold=True)

    course_code = header.get("course_code")
    course_title = header.get("course_title")
    if course_code and course_title:
        add_center_line(f"{course_code} - {course_title}", bold=True)
    else:
        add_center_line(course_title, bold=True)

    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    left = table.rows[0].cells[0]
    right = table.rows[0].cells[1]
    left.text = f"Time: {header.get('time') or '__________'}"
    right.text = f"Date: {header.get('date') or '__________'}"

    max_marks = header.get("max_marks")
    if max_marks:
        p = doc.add_paragraph()
        p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        p.add_run(f"Max. Marks: {max_marks}")

    def add_part(title, instruction, questions, start_no, with_or):
        p = doc.add_paragraph()
        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        p.add_run(title).bold = True
        if instruction:
            p2 = doc.add_paragraph()
            p2.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            p2.add_run(instruction)

        t = doc.add_table(rows=1, cols=4)
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr = t.rows[0].cells
        hdr[0].text = "S.No."
        hdr[1].text = "Questions"
        hdr[2].text = "Course Outcome"
        hdr[3].text = "Bloom's Taxonomy level"

        for i, q in enumerate(questions, start=0):
            no = start_no + i
            if with_or:
                row_a = t.add_row().cells
                row_a[0].text = f"{no}(a)"
                row_a[1].text = q.get("question", "")
                row_a[2].text = q.get("co", "")
                row_a[3].text = q.get("bloom", "")

                or_row = t.add_row().cells
                or_row[1].text = "OR"
                or_row[1].paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

                row_b = t.add_row().cells
                row_b[0].text = f"{no}(b)"
                row_b[1].text = q.get("or_question", "")
                row_b[2].text = q.get("or_co", "")
                row_b[3].text = q.get("or_bloom", "")
            else:
                row = t.add_row().cells
                row[0].text = str(no)
                row[1].text = q.get("question", "")
                row[2].text = q.get("co", "")
                row[3].text = q.get("bloom", "")

    part_a = qp.get("part_a", [])
    part_b = qp.get("part_b", [])
    part_c = qp.get("part_c", [])

    add_part(f"PART - A ({part_a_count} x 2 = {part_a_count * 2} marks)", "Answer all the Questions", part_a, 1, False)
    add_part("PART - B (2 x 16 = 32 marks)", None, part_b, part_a_count + 1, True)
    add_part("PART - C (1 x 8 = 8 marks)", None, part_c, part_a_count + part_b_count + 1, True)

    out = BytesIO()
    doc.save(out)
    out.seek(0)
    return out
