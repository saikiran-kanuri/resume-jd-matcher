"""
Tests for backend/services/skill_extraction.py

We test against small inline strings rather than real resume/JD files —
matcher correctness only depends on text content, not on where the text
came from (mirrors the same decoupling rationale as pdf_parser.py).
"""
import pytest
from backend.services.skill_extraction import (
    extract_skills,
    extract_skill_frequencies,
    get_skill_type,
)


def test_basic_skill_extraction():
    text = "I know Python, Docker, and SQL."
    skills = extract_skills(text)

    assert "Python" in skills
    assert "Docker" in skills
    assert "SQL" in skills


def test_alias_resolves_to_canonical_name():
    text = "Experienced with JS and ML."
    skills = extract_skills(text)

    assert "JavaScript" in skills
    assert "Machine Learning" in skills
    assert "JS" not in skills
    assert "ML" not in skills


def test_case_insensitive_matching():
    text = "python, DOCKER, ReAcT"
    skills = extract_skills(text)

    assert "Python" in skills
    assert "Docker" in skills
    assert "React" in skills


def test_multiword_skill_is_matched_as_one_unit():
    text = "Strong background in Machine Learning and Natural Language Processing."
    skills = extract_skills(text)

    assert "Machine Learning" in skills
    assert "Natural Language Processing" in skills


def test_no_false_positive_on_unrelated_text():
    text = "The weather today is sunny and the meeting starts at noon."
    skills = extract_skills(text)

    assert skills == set()


def test_frequency_counts_repeated_mentions():
    text = "Python is required. Python experience is a must. We use Python daily."
    freqs = extract_skill_frequencies(text)

    assert freqs["Python"] == 3


def test_frequency_dict_only_includes_found_skills():
    text = "We use Docker here."
    freqs = extract_skill_frequencies(text)

    assert freqs == {"Docker": 1}
    assert "Kubernetes" not in freqs


def test_get_skill_type_returns_hard_for_technical_skill():
    assert get_skill_type("Python") == "hard"
    assert get_skill_type("Docker") == "hard"


def test_get_skill_type_returns_soft_for_soft_skill():
    assert get_skill_type("Communication") == "soft"
    assert get_skill_type("Leadership") == "soft"


def test_get_skill_type_raises_for_unknown_skill():
    with pytest.raises(ValueError):
        get_skill_type("SomeSkillNotInTaxonomy")


def test_plural_acronym_forms_are_matched():
    # Regression guard: "CNNs" (plural, no space before 's') failed to
    # match the "CNN" pattern until we added explicit plural aliases.
    # This locks that fix in place.
    text = "I worked with CNNs, RNNs, and LSTMs on this project."
    skills = extract_skills(text)

    assert "CNN" in skills
    assert "RNN" in skills
    assert "LSTM" in skills


def test_architecture_names_are_recognized():
    text = "Used EfficientNet, ResNet50, and MobileNetV2 for the classifier."
    skills = extract_skills(text)

    assert "EfficientNet" in skills
    assert "ResNet" in skills
    assert "MobileNet" in skills
def test_get_skill_type_is_case_insensitive():
    assert get_skill_type("communication") == "soft"
    assert get_skill_type("PYTHON") == "hard"
    