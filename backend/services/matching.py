"""
backend/services/matching.py

Cross-text logic that combines resume and JD data — functions here
need BOTH texts together, unlike skill_extraction.py (single-text
extraction) or embedding.py (also cross-text, but for the similarity
score rather than skill-level detail).
"""
import re
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

REQUIRED_HEADINGS = [
    "requirements",
    "required qualifications",
    "minimum qualifications",
    "required skills",
]

# Headings that introduce "nice to have" content
PREFERRED_HEADINGS = [
    "preferred qualifications",
    "preferred skills",
    "preferred (not required)",
    "desired qualifications",
]


def _split_into_sections(jd_text: str) -> list[tuple[str, str]]:
    """
    Splits JD text into (heading_label, section_body) pairs, where
    heading_label is one of 'required', 'preferred', or 'none' (for
    text before any recognized heading, or under an unrecognized one).

    A line only counts as a heading if it consists solely of one of the
    known heading phrases (case-insensitive, optional trailing colon) —
    this guards against matching the word "requirements" when it
    appears mid-sentence (e.g. "...business requirements, design...").
    """
    lines = jd_text.splitlines()
    sections: list[tuple[str, list[str]]] = [("none", [])]

    for line in lines:
        stripped = line.strip().rstrip(":").lower()

        if stripped in REQUIRED_HEADINGS:
            sections.append(("required", []))
        elif stripped in PREFERRED_HEADINGS:
            sections.append(("preferred", []))
        else:
            sections[-1][1].append(line)

    return [(label, "\n".join(body)) for label, body in sections]


def get_skill_section_category(jd_text: str, skill: str) -> str:
    """
    Returns 'required', 'preferred', or 'none' depending on which JD
    section (by heading) the skill appears under. If the skill appears
    under multiple sections, 'required' takes priority over 'preferred',
    which takes priority over 'none' — since a skill mentioned in ANY
    required-type section should be treated as required overall.
    """
    sections = _split_into_sections(jd_text)

    found_categories = {
        label for label, body in sections
        if skill.lower() in body.lower()
    }

    if "required" in found_categories:
        return "required"
    if "preferred" in found_categories:
        return "preferred"
    return "none"