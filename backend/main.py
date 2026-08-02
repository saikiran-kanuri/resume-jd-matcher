"""
backend/main.py

FastAPI app — thin wiring layer only. All actual logic lives in
backend/services/; this file's job is: receive request, call services
in the right order, shape the response via Pydantic models.
"""
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pdfminer.pdfparser import PDFSyntaxError

from backend.services.pdf_parser import extract_text_from_pdf
from backend.services.embedding import compute_match_score
from backend.services.matching import (
    get_matched_skills,
    get_missing_skills_with_frequency,
    generate_suggestions,
)
from backend.models.schemas import MatchResponse

app = FastAPI(title="Resume-JD Match Scorer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # local Streamlit dev
        "https://resume-jd-matcher-app.streamlit.app",  # production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/match", response_model=MatchResponse)
async def match(resume: UploadFile, jd_text: str = Form(...)):
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="jd_text cannot be empty.")

    file_bytes = await resume.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Resume file exceeds 5MB limit.")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)

    try:
        resume_text = extract_text_from_pdf(tmp_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PDFSyntaxError:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid PDF.",
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    score = compute_match_score(resume_text, jd_text)
    matched = get_matched_skills(resume_text, jd_text)
    missing = get_missing_skills_with_frequency(resume_text, jd_text)
    suggestions = generate_suggestions(resume_text, jd_text)

    return MatchResponse(
        score=score,
        matched_skills=sorted(matched),
        missing_skills=list(missing.keys()),
        suggestions=suggestions,
    )