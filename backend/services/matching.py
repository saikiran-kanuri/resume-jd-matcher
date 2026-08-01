"""
backend/services/matching.py

Cross-text logic that combines resume and JD data — functions here
need BOTH texts together, unlike skill_extraction.py (single-text
extraction) or embedding.py (also cross-text, but for the similarity
score rather than skill-level detail).
"""
from backend.services.skill_extraction import extract_skills, extract_skill_frequencies


def get_missing_skills_with_frequency(resume_text: str, jd_text: str) -> dict[str, int]:
    """
    Returns skills present in the JD but absent from the resume,
    mapped to how many times each appears in the JD.

    This is the foundational data for Phase 3b's suggestion priority
    scoring (see Section 5 of the project doc) — JD term frequency is
    one of three signals (alongside section placement and hard/soft
    skill type) that determine how urgently a missing skill should be
    flagged to the user.
    """
    resume_skills = extract_skills(resume_text)
    jd_frequencies = extract_skill_frequencies(jd_text)

    return {
        skill: count
        for skill, count in jd_frequencies.items()
        if skill not in resume_skills
    }