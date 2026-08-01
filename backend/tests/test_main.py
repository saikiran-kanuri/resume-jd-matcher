"""
Tests for backend/main.py — the FastAPI /match and /health endpoints.
Uses FastAPI's TestClient, which runs the app in-process (no real
server/network needed), so these tests are fast and self-contained.
Fixture files live in backend/tests/fixtures/ so tests don't depend on
files outside the repo (e.g. a real personal resume).
"""
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
VALID_PDF = FIXTURES_DIR / "sample_resume.pdf"
INVALID_PDF = FIXTURES_DIR / "invalid.txt"


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_match_rejects_empty_jd_text():
    with open(VALID_PDF, "rb") as f:
        response = client.post(
            "/match",
            files={"resume": ("sample_resume.pdf", f, "application/pdf")},
            data={"jd_text": "   "},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "jd_text cannot be empty."


def test_match_rejects_invalid_pdf():
    with open(INVALID_PDF, "rb") as f:
        response = client.post(
            "/match",
            files={"resume": ("invalid.txt", f, "text/plain")},
            data={"jd_text": "Looking for a Python developer."},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded file is not a valid PDF."


def test_match_returns_full_response_for_valid_input():
    jd_text = "Looking for a Python developer with Docker and AWS experience."

    with open(VALID_PDF, "rb") as f:
        response = client.post(
            "/match",
            files={"resume": ("sample_resume.pdf", f, "application/pdf")},
            data={"jd_text": jd_text},
        )

    assert response.status_code == 200
    body = response.json()

    assert "score" in body
    assert 0 <= body["score"] <= 100
    assert "Python" in body["matched_skills"]
    assert "Docker" in body["matched_skills"]
    assert "AWS" in body["missing_skills"]
    assert isinstance(body["suggestions"], list)