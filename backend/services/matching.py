"""
backend/services/matching.py

Cross-text logic that combines resume and JD data — functions here
need BOTH texts together, unlike skill_extraction.py (single-text
extraction) or embedding.py (also cross-text, but for the similarity
score rather than skill-level detail).
"""
import re
from backend.services.skill_extraction import (
    extract_skills,
    extract_skill_frequencies,
    get_skill_type,
)


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

# Weights for the priority_score formula (Section 5.1 of the project doc).
# Section placement is weighted highest — an employer explicitly labeling
# a skill as "required" is a stronger urgency signal than inferring it
# from repetition count or skill type alone.
JD_FREQUENCY_WEIGHT = 2
SECTION_WEIGHT = 3
SKILL_TYPE_WEIGHT = 2

# Caps JD term frequency's contribution — beyond 5 mentions, additional
# repetition doesn't meaningfully increase urgency.
FREQUENCY_CAP = 5

SECTION_SCORES = {
    "required": 1.0,
    "preferred": 0.5,
    "none": 0.0,
}


def compute_priority_score(skill: str, jd_frequency: int, jd_text: str) -> float:
    """
    Combines the three Phase 3b signals (JD term frequency, section
    placement, hard/soft skill type) into a single priority score, per
    the formula in Section 5.1 of the project doc:

        priority_score = (jd_frequency_weight * jd_term_frequency)
                        + (section_weight * is_in_requirements_section)
                        + (skill_type_weight * is_hard_skill)

    Each signal is normalized to a 0-1 scale before weighting, so the
    weights alone control relative importance. Max possible score is
    JD_FREQUENCY_WEIGHT + SECTION_WEIGHT + SKILL_TYPE_WEIGHT.
    """
    frequency_score = min(jd_frequency, FREQUENCY_CAP) / FREQUENCY_CAP

    section_category = get_skill_section_category(jd_text, skill)
    section_score = SECTION_SCORES[section_category]

    skill_type = get_skill_type(skill)
    type_score = 1.0 if skill_type == "hard" else 0.0

    return (
        JD_FREQUENCY_WEIGHT * frequency_score
        + SECTION_WEIGHT * section_score
        + SKILL_TYPE_WEIGHT * type_score
    )

def get_priority_bucket(score: float) -> str:
    """
    Buckets a priority_score into 'high', 'medium', or 'low', using
    fixed thresholds over the score's full possible range (0 to
    JD_FREQUENCY_WEIGHT + SECTION_WEIGHT + SKILL_TYPE_WEIGHT = 7).

    Fixed thresholds (rather than ranking within one resume's flagged
    list) so 'High' means the same thing — genuinely high absolute
    urgency — across every resume/JD pair, not just 'worst of this
    particular batch'.
    """
    max_score = JD_FREQUENCY_WEIGHT + SECTION_WEIGHT + SKILL_TYPE_WEIGHT
    high_threshold = max_score * (2 / 3)
    medium_threshold = max_score * (1 / 3)

    if score >= high_threshold:
        return "high"
    if score >= medium_threshold:
        return "medium"
    return "low"