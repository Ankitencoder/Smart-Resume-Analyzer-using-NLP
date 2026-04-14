import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from flask import Flask, jsonify, render_template, request
from PyPDF2 import PdfReader
import spacy
from werkzeug.utils import secure_filename
import zipfile
import xml.etree.ElementTree as ET


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {"pdf", "docx"}


try:
    NLP = spacy.load("en_core_web_sm")
except OSError:
    NLP = spacy.blank("en")


COMMON_SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "sql",
    "flask",
    "django",
    "react",
    "node",
    "nlp",
    "machine learning",
    "deep learning",
    "tensorflow",
    "pytorch",
    "aws",
    "docker",
    "kubernetes",
    "git",
    "linux",
    "api",
    "html",
    "css",
    "pandas",
    "numpy",
    "scikit-learn",
}


@dataclass
class ResumeAnalysis:
    skills: List[str]
    score: int
    missing_keywords: List[str]
    suggestions: List[str]

    def to_dict(self) -> Dict:
        return {
            "skills": self.skills,
            "score": self.score,
            "missing_keywords": self.missing_keywords,
            "suggestions": self.suggestions,
        }


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def extract_text_from_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as docx_zip:
        with docx_zip.open("word/document.xml") as document_xml:
            tree = ET.parse(document_xml)
    root = tree.getroot()
    namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    text_nodes = root.findall(".//w:t", namespaces)
    return " ".join(node.text for node in text_nodes if node.text)


def extract_text(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    if ext == ".docx":
        return extract_text_from_docx(file_path)
    raise ValueError("Unsupported file type")


def extract_skills(text: str) -> List[str]:
    lowered = text.lower()
    found = sorted(skill for skill in COMMON_SKILLS if skill in lowered)

    if not found:
        doc = NLP(text)
        noun_chunks = {chunk.text.lower().strip() for chunk in doc.noun_chunks}
        found = sorted(chunk for chunk in noun_chunks if len(chunk.split()) <= 3)

    return found


def tokenize_keywords(text: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+\-#\.]{1,}", text.lower())
    return [tok for tok in tokens if len(tok) > 2]


def score_resume(resume_text: str, jd_text: str, skills: List[str]) -> ResumeAnalysis:
    score = 50
    suggestions = []

    if len(skills) >= 8:
        score += 20
    elif len(skills) >= 4:
        score += 10
    else:
        suggestions.append("Add more role-specific skills in a dedicated Skills section.")

    if re.search(r"\b(experience|work history|professional experience)\b", resume_text.lower()):
        score += 10
    else:
        suggestions.append("Include a clear Experience section with impact-oriented bullet points.")

    if re.search(r"\b(projects?)\b", resume_text.lower()):
        score += 5
    else:
        suggestions.append("Add 1-2 relevant projects with technologies and measurable outcomes.")

    jd_keywords = set(tokenize_keywords(jd_text))
    resume_keywords = set(tokenize_keywords(resume_text))

    missing_keywords = sorted(list(jd_keywords - resume_keywords))[:15]
    matched = len(jd_keywords & resume_keywords)
    if jd_keywords:
        score += int((matched / len(jd_keywords)) * 15)

    if missing_keywords:
        suggestions.append("Align your resume language with the job description's key terms.")

    score = max(0, min(100, score))
    return ResumeAnalysis(skills=skills, score=score, missing_keywords=missing_keywords, suggestions=suggestions)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_resume():
    if "resume" not in request.files:
        return jsonify({"error": "Resume file is required."}), 400

    resume_file = request.files["resume"]
    job_description = request.form.get("job_description", "")

    if resume_file.filename == "":
        return jsonify({"error": "Please select a file."}), 400

    if not allowed_file(resume_file.filename):
        return jsonify({"error": "Only PDF and DOCX files are supported."}), 400

    with tempfile.TemporaryDirectory() as tmp_dir:
        filename = secure_filename(resume_file.filename)
        save_path = Path(tmp_dir) / filename
        resume_file.save(save_path)

        try:
            resume_text = extract_text(save_path)
            skills = extract_skills(resume_text)
            analysis = score_resume(resume_text, job_description, skills)
            return jsonify(analysis.to_dict())
        except Exception as exc:
            return jsonify({"error": f"Failed to analyze resume: {exc}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
