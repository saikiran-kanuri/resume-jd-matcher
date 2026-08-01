"""
Tests for backend/services/matching.py — get_missing_skills_with_frequency.

We use short synthetic resume/JD strings here (not real PDFs or
calibration files) so each test isolates one specific behavior of the
set-difference + frequency-lookup logic, independent of real-world
text noise.
"""
from backend.services.matching import (
    get_missing_skills_with_frequency,
    get_skill_section_category,
    compute_priority_score,
    get_priority_bucket,
    build_suggestion_message,
    get_missing_section_suggestions,
    generate_suggestions,
)


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

def test_priority_score_is_high_for_frequent_required_hard_skill():
    jd = """
Requirements:
Docker
We need someone with Docker Docker Docker Docker experience.
"""
    score = compute_priority_score("Docker", jd_frequency=4, jd_text=jd)

    assert score == 6.6


def test_priority_score_is_low_for_rare_unlisted_soft_skill():
    jd = "We value Communication in this role."

    score = compute_priority_score("Communication", jd_frequency=1, jd_text=jd)

    assert score == 0.4


def test_priority_score_gives_partial_credit_for_preferred_section():
    jd = """
Preferred Qualifications:
Kubernetes
"""
    score = compute_priority_score("Kubernetes", jd_frequency=1, jd_text=jd)

    # freq: 1/5 * 2 = 0.4, section: preferred = 0.5 * 3 = 1.5, type: hard = 1 * 2 = 2
    assert score == 3.9


def test_priority_score_caps_frequency_contribution_at_five_mentions():
    jd_low_freq = "Requirements:\nDocker\nDocker experience needed."
    jd_high_freq = "Requirements:\nDocker\n" + "Docker " * 20

    score_at_cap = compute_priority_score("Docker", jd_frequency=5, jd_text=jd_low_freq)
    score_above_cap = compute_priority_score("Docker", jd_frequency=20, jd_text=jd_high_freq)

    assert score_at_cap == score_above_cap


def test_priority_bucket_high_for_score_at_or_above_two_thirds_of_max():
    assert get_priority_bucket(6.6) == "high"
    assert get_priority_bucket(4.6667) == "high"


def test_priority_bucket_medium_for_score_in_middle_third():
    assert get_priority_bucket(3.5) == "medium"
    assert get_priority_bucket(2.3334) == "medium"


def test_priority_bucket_low_for_score_below_one_third_of_max():
    assert get_priority_bucket(0.4) == "low"
    assert get_priority_bucket(2.0) == "low"

def test_missing_section_flagged_when_jd_wants_projects_but_resume_has_none():
    jd = "We want to see your GitHub and a strong portfolio of side projects."
    resume = "Experience\nSoftware Engineer at XYZ.\n\nSkills\nPython, Docker."

    suggestions = get_missing_section_suggestions(resume, jd)

    assert len(suggestions) == 1
    assert "Projects" in suggestions[0]


def test_missing_section_not_flagged_when_resume_has_projects_section():
    jd = "We want to see your GitHub and a strong portfolio of side projects."
    resume = (
        "Experience\nSoftware Engineer at XYZ.\n\n"
        "Projects\nBuilt a resume-JD matcher using sentence embeddings."
    )

    suggestions = get_missing_section_suggestions(resume, jd)

    assert suggestions == []


def test_missing_section_not_flagged_when_jd_does_not_mention_projects():
    jd = "Looking for a backend engineer with strong Python and SQL skills."
    resume = "Experience\nSoftware Engineer at XYZ."

    suggestions = get_missing_section_suggestions(resume, jd)

    assert suggestions == []


def test_build_suggestion_message_matches_template_exactly():
    jd = "Requirements:\nKubernetes\nKubernetes Kubernetes Kubernetes"
    message = build_suggestion_message("Kubernetes", jd_frequency=4, jd_text=jd)

    expected = (
        "Your resume doesn't mention 'Kubernetes', which appears 4 time(s) "
        "in the job description (listed under 'Requirements'). Consider "
        "adding it if you have relevant experience."
    )
    assert message == expected

def test_missing_section_flagged_when_jd_wants_skills_but_resume_has_none():
    jd = "Our tech stack includes Python and React."
    resume = "Experience\nSoftware Engineer at XYZ.\n\nProjects\nBuilt a tool."

    suggestions = get_missing_section_suggestions(resume, jd)

    assert len(suggestions) == 1
    assert "Skills" in suggestions[0]


def test_missing_section_not_flagged_when_resume_has_skills_section():
    jd = "Our tech stack includes Python and React."
    resume = (
        "Experience\nSoftware Engineer at XYZ.\n\n"
        "Skills\nPython, React, Docker."
    )

    suggestions = get_missing_section_suggestions(resume, jd)

    assert suggestions == []


def test_missing_section_flags_both_projects_and_skills_when_both_apply():
    jd = "Show us your GitHub portfolio and tell us your tech stack."
    resume = "Experience\nSoftware Engineer at XYZ."

    suggestions = get_missing_section_suggestions(resume, jd)

    assert len(suggestions) == 2
    combined = " ".join(suggestions)
    assert "Projects" in combined
    assert "Skills" in combined

def test_generate_suggestions_puts_structural_suggestions_first():
    jd = "Show us your GitHub portfolio. Looking for a Python developer."
    resume = "Experience\nSoftware Engineer at XYZ."

    suggestions = generate_suggestions(resume, jd)

    assert suggestions[0]["type"] == "missing_section"


def test_generate_suggestions_ranks_missing_skills_by_priority_score():
    jd = """
Requirements:
Kubernetes
Kubernetes Kubernetes Kubernetes

Nice to have: communication skills.
"""
    resume = "Experience\nSoftware Engineer at XYZ.\n\nProjects\nBuilt a tool."

    suggestions = generate_suggestions(resume, jd)

    skill_suggestions = [s for s in suggestions if s["type"] == "missing_skill"]
    assert skill_suggestions[0]["skill"] == "Kubernetes"
    assert skill_suggestions[0]["priority"] == "high"


def test_generate_suggestions_respects_max_suggestions_cap():
    jd = """
Requirements:
Python, Docker, Kubernetes, AWS, React, SQL, Git, Java, Linux, Go
"""
    resume = "Experience\nSoftware Engineer at XYZ."

    suggestions = generate_suggestions(resume, jd, max_suggestions=3)

    assert len(suggestions) == 3


def test_generate_suggestions_returns_empty_list_when_nothing_missing():
    jd = "Looking for a Python developer."
    resume = (
        "Experience\nSoftware Engineer at XYZ.\n\n"
        "Skills\nPython.\n\nProjects\nBuilt a tool."
    )

    suggestions = generate_suggestions(resume, jd)

    assert suggestions == []


def test_generate_suggestions_message_shape_matches_expected_schema():
    jd = "Requirements:\nKubernetes\nKubernetes Kubernetes"
    resume = "Experience\nSoftware Engineer at XYZ.\n\nProjects\nBuilt a tool.\n\nSkills\nPython."

    suggestions = generate_suggestions(resume, jd)
    skill_suggestion = next(s for s in suggestions if s["type"] == "missing_skill")

    assert set(skill_suggestion.keys()) == {
        "type", "skill", "priority", "jd_frequency", "reason", "message"
    }