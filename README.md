# Smart Resume Analyzer (AI-powered)

A web app that analyzes resumes (PDF/DOCX), extracts skills, computes a resume score, and compares keyword coverage against a job description.

## Features
- Skill extraction from uploaded resume text
- Resume scoring (0-100)
- Suggestions for resume improvement
- Keyword matching with job descriptions

## Tech Stack
- Frontend: HTML, CSS, JavaScript
- Backend: Flask (Python)
- NLP: spaCy
- File handling: PyPDF2 (PDF) + DOCX XML parsing

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Usage
1. Upload a `.pdf` or `.docx` resume.
2. Paste a target job description.
3. Click **Analyze Resume**.
4. Review extracted skills, score, missing keywords, and suggestions.
