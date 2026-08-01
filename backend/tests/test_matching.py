"""
Tests for backend/services/matching.py — get_missing_skills_with_frequency.

We use short synthetic resume/JD strings here (not real PDFs or
calibration files) so each test isolates one specific behavior of the
set-difference + frequency-lookup logic, independent of real-world
text noise.
"""
from backend.services.matching import get_missing_skills_with_frequency


def test_skill_in_jd_but_not_resume_is_flagged_as_missing():
    resume = "Experienced Python developer with FastAPI skills."
    jd = "Looking for a Python developer with Kubernetes experience."

    result = get_missing_skills_with_frequency(resume, jd)

    assert "Kubernetes" in result
    assert result["Kubernetes"] == 1


def test_skill_present_in_both_is_not_flagged_as_missing():
    resume = "Experienced Python developer skilled in Docker."
    jd = "Looking for a Python developer with Docker experience."

    result = get_missing_skills_with_frequency(resume, jd)

    assert "Docker" not in result
    assert "Python" not in result


def test_jd_frequency_count_is_preserved_in_result():
    resume = "Experienced software engineer."
    jd = "Kubernetes, Kubernetes, and more Kubernetes experience required."

    result = get_missing_skills_with_frequency(resume, jd)

    assert result["Kubernetes"] == 3


def test_empty_jd_returns_empty_result():
    resume = "Experienced Python developer with Docker and Kubernetes skills."
    jd = ""

    result = get_missing_skills_with_frequency(resume, jd)

    assert result == {}


def test_empty_resume_returns_all_jd_skills_as_missing():
    resume = ""
    jd = "Looking for a Python developer with Docker experience."

    result = get_missing_skills_with_frequency(resume, jd)

    assert "Python" in result
    assert "Docker" in result