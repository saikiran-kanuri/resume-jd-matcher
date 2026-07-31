"""
pdf_parser.py

Two independent responsibilities, kept deliberately separate:

1. extract_text_from_pdf(): mechanical PDF -> plain text extraction.
2. detect_sections(): semantic plain-text -> labeled sections (Skills /
   Experience / Projects / other), using regex heading detection.

Why separate: section detection should work on ANY string (pasted text,
test fixtures, future non-PDF sources), not just on freshly-extracted PDF
text. This also makes section detection trivial to unit test without
needing real PDF files.
"""

import re
from pathlib import Path
from typing import Union

import pdfplumber


def extract_text_from_pdf(file_path: Union[str, Path]) -> str:
    """
    Extract plain text from a PDF file, page by page, preserving reading
    order top-to-bottom. Returns a single joined string with pages
    separated by a newline.

    Raises:
        FileNotFoundError: if file_path doesn't exist.
        ValueError: if the PDF has no extractable text (e.g. a scanned
            image PDF with no OCR layer) — we surface this clearly rather
            than silently returning an empty string, since a silent empty
            string would quietly break every downstream stage.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    pages_text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                pages_text.append(page_text)

    full_text = "\n".join(pages_text).strip()

    if not full_text:
        raise ValueError(
            f"No extractable text found in {file_path}. "
            "This may be a scanned/image-only PDF with no text layer."
        )

    return full_text


# ---------------------------------------------------------------------------
# Section detection
# ---------------------------------------------------------------------------

# Canonical section -> list of heading phrases we should recognize.
# Kept as a simple, editable mapping (mirrors the taxonomy philosophy from
# Phase 2: explainable and easy to extend, no training data required).
SECTION_HEADING_PATTERNS = {
    "skills": [
        r"technical skills",
        r"core skills",
        r"skills? (and|&) tools",
        r"skills?",
        r"technologies",
    ],
    "experience": [
        r"work experience",
        r"professional experience",
        r"employment history",
        r"experience",
    ],
    "projects": [
        r"projects?",
        r"personal projects",
        r"academic projects",
    ],
    "education": [
        r"education",
        r"academic background",
    ],
    "summary": [
        r"summary",
        r"professional summary",
        r"about me",
        r"objective",
    ],

}

# Max words for a line to be considered a heading candidate at all.
# Real headings are short ("Technical Skills"); sentences are not.
MAX_HEADING_WORDS = 5


def _build_heading_regex() -> re.Pattern:
    """
    Compile one regex that matches a full line consisting of (optionally)
    a known heading phrase, optionally followed by a colon, optionally
    surrounded by whitespace. Anchored to the whole line (^...$) so we
    don't match a heading phrase occurring mid-sentence.
    """
    all_phrases = [
        phrase
        for phrases in SECTION_HEADING_PATTERNS.values()
        for phrase in phrases
    ]
    # Sort longest-first so e.g. "technical skills" matches before "skills".
    all_phrases.sort(key=len, reverse=True)
    combined = "|".join(all_phrases)
    return re.compile(rf"^\s*({combined})\s*:?\s*$", re.IGNORECASE)


_HEADING_RE = _build_heading_regex()


def _classify_heading(line: str) -> Union[str, None]:
    """Return the canonical section name for a line, or None if it's not
    a recognized heading."""
    match = _HEADING_RE.match(line)
    if not match:
        return None
    matched_phrase = match.group(1).lower()
    for section, phrases in SECTION_HEADING_PATTERNS.items():
        for phrase in phrases:
            if re.fullmatch(phrase, matched_phrase, re.IGNORECASE):
                return section
    return None


def detect_sections(text: str) -> dict:
    """
    Split resume text into labeled sections based on heading lines.

    Returns a dict with keys: "skills", "experience", "projects",
    "education", "other". Any key with no detected content is an empty
    string. "other" captures everything before the first recognized
    heading (e.g. name, contact info, summary).

    Approach: walk line by line; a line is a heading candidate only if
    it's short (<= MAX_HEADING_WORDS words) and matches a known heading
    phrase pattern. Once a heading is found, all following lines belong
    to that section until the next heading.
    """
    sections = {key: [] for key in SECTION_HEADING_PATTERNS}
    sections["other"] = []

    current_section = "other"

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        word_count = len(line.split())
        if word_count <= MAX_HEADING_WORDS:
            classified = _classify_heading(line)
            if classified:
                current_section = classified
                continue  # heading line itself isn't content

        sections[current_section].append(line)

    return {key: "\n".join(lines).strip() for key, lines in sections.items()}
