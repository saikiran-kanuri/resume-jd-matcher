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

from backend.services.matching import get_skill_section_category


def test_skill_under_requirements_heading_is_required():
    jd = """
Requirements:
Python, Docker, and Kubernetes experience needed.
"""
    assert get_skill_section_category(jd, "Python") == "required"


def test_skill_under_preferred_heading_is_preferred():
    jd = """
Requirements:
Python experience needed.
Preferred Skills:
Kubernetes experience is a plus.
"""
    assert get_skill_section_category(jd, "Kubernetes") == "preferred"


def test_skill_with_no_recognized_section_is_none():
    jd = """
About the role:
We use Python and Docker daily.
"""
    assert get_skill_section_category(jd, "Python") == "none"


def test_alternate_required_heading_phrasings_are_recognized():
    jd_minimum = """
Minimum Qualifications
Python experience required.
"""
    jd_required_skills = """
Required Skills:
Azure knowledge needed.
"""
    assert get_skill_section_category(jd_minimum, "Python") == "required"
    assert get_skill_section_category(jd_required_skills, "Azure") == "required"


def test_alternate_preferred_heading_phrasing_is_recognized():
    jd = """
Desired Qualifications:
Kubernetes experience is a plus.
"""
    assert get_skill_section_category(jd, "Kubernetes") == "preferred"


def test_heading_like_word_inside_a_sentence_is_not_misclassified():
    # "requirements" appears inside a sentence here, not as its own
    # heading line — it must NOT trigger a switch to the "required"
    # section. Mirrors the same guard tested in test_pdf_parser.py.
    jd = """
About the role:
We analyse highly complex business requirements as part of this role.
Python experience is a plus.
"""
    assert get_skill_section_category(jd, "Python") == "none"


def test_skill_in_both_required_and_preferred_resolves_to_required():
    jd = """
Requirements:
Python experience needed.
Preferred Skills:
Python knowledge is also a plus, plus Docker.
"""
    assert get_skill_section_category(jd, "Python") == "required"