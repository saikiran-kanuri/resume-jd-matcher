"""
Tests for backend/services/pdf_parser.py — section detection only.

We deliberately don't test extract_text_from_pdf() with a real PDF here;
that would need a binary fixture file. Section detection is tested
directly on plain strings, which is exactly the point of keeping the two
functions decoupled (see module docstring in pdf_parser.py).
"""

from backend.services.pdf_parser import detect_sections


def test_basic_sections_are_detected():
    text = """
John Doe
[email protected]

Skills
Python, FastAPI, Docker

Experience
Software Engineer at Acme Corp - built things

Projects
Resume Matcher - a tool that scores resumes
"""
    result = detect_sections(text)

    assert "Python, FastAPI, Docker" in result["skills"]
    assert "Software Engineer at Acme Corp" in result["experience"]
    assert "Resume Matcher" in result["projects"]
    assert "John Doe" in result["other"]
    assert result["education"] == ""


def test_heading_synonyms_are_recognized():
    text = """
Technical Skills
Java, C++

Work Experience
Backend dev at StartupX

Academic Projects
Chess engine in Python
"""
    result = detect_sections(text)

    assert "Java, C++" in result["skills"]
    assert "Backend dev at StartupX" in result["experience"]
    assert "Chess engine in Python" in result["projects"]


def test_heading_like_word_inside_a_sentence_is_not_misclassified():
    # "experience" appears inside a sentence here, not as its own heading
    # line — it must NOT trigger a switch to the "experience" section.
    # The sentence lives under "Summary" (a real heading), so it should
    # land in result["summary"], not get misclassified into "experience".
    text = """
Summary
I have 5 years of experience building backend systems and APIs.

Skills
Python, SQL
"""
    result = detect_sections(text)

    assert "5 years of experience" in result["summary"]
    assert "5 years of experience" not in result["experience"]
    assert "Python, SQL" in result["skills"]


def test_empty_string_returns_all_empty_sections():
    result = detect_sections("")

    assert result["skills"] == ""
    assert result["experience"] == ""
    assert result["projects"] == ""
    assert result["education"] == ""
    assert result["other"] == ""


def test_missing_sections_are_empty_not_missing_keys():
    text = "Skills\nPython"
    result = detect_sections(text)

    for key in ["skills", "experience", "projects", "education", "other"]:
        assert key in result


def test_case_insensitive_heading_match():
    text = "SKILLS\nGo, Rust\n\nprojects\nCLI tool"
    result = detect_sections(text)

    assert "Go, Rust" in result["skills"]
    assert "CLI tool" in result["projects"]

def test_summary_section_is_detected():
    text = """
John Doe

Summary
Backend engineer with 3 years of experience in distributed systems.

Skills
Go, Kubernetes
"""
    result = detect_sections(text)

    assert "Backend engineer with 3 years" in result["summary"]
    assert "Go, Kubernetes" in result["skills"]