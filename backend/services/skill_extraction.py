"""
skill_extraction.py

Loads the skill taxonomy (backend/data/skill_taxonomy.json) and uses
spaCy's PhraseMatcher to detect which taxonomy skills appear in a given
text (resume or JD).

Design notes:
- The spaCy model and PhraseMatcher are built ONCE at module import time,
  not per-call — loading a spaCy pipeline is relatively expensive, and
  this module will be called repeatedly (once per resume, once per JD,
  potentially many times under FastAPI). Building it once and reusing it
  mirrors the same "load once at startup" principle the project doc uses
  for the sentence-transformers model in Phase 3a.
- Every alias AND the canonical name are registered as match patterns,
  but all matches resolve back to the canonical `name` — so "JS" and
  "JavaScript" both count as the same skill in the output. This is what
  makes the matcher useful: without alias resolution, a resume saying
  "JS" wouldn't match a JD asking for "JavaScript" even though they mean
  the same thing.
- Matching is case-insensitive (attr="LOWER") since resumes/JDs are
  inconsistently capitalized.
"""

import json
from pathlib import Path
from typing import Dict, Set

import spacy
from spacy.matcher import PhraseMatcher

TAXONOMY_PATH = Path(__file__).parent.parent / "data" / "skill_taxonomy.json"


def _load_taxonomy() -> list:
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_matcher(nlp, taxonomy: list) -> tuple:
    """
    Build a PhraseMatcher where every alias and canonical name is a
    pattern, and return (matcher, lookup) where lookup maps the spaCy
    match_id back to the canonical skill name and its type (hard/soft).
    """
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    lookup: Dict[str, dict] = {}

    for skill in taxonomy:
        canonical_name = skill["name"]
        skill_type = skill.get("type", "hard")

        match_id = canonical_name

        surface_forms = [canonical_name] + skill.get("aliases", [])
        patterns = [nlp.make_doc(form) for form in surface_forms]
        matcher.add(match_id, patterns)

        lookup[match_id] = {"name": canonical_name, "type": skill_type}

    return matcher, lookup


_nlp = spacy.load("en_core_web_sm", disable=["ner", "parser", "lemmatizer"])
_taxonomy = _load_taxonomy()
_matcher, _lookup = _build_matcher(_nlp, _taxonomy)


def extract_skills(text: str) -> Set[str]:
    """
    Return the set of canonical skill names found anywhere in the text.
    Use this for resumes, or anywhere only presence/absence matters.
    """
    doc = _nlp(text)
    matches = _matcher(doc)

    found = set()
    for match_id, start, end in matches:
        match_id_str = _nlp.vocab.strings[match_id]
        found.add(_lookup[match_id_str]["name"])

    return found


def extract_skill_frequencies(text: str) -> Dict[str, int]:
    """
    Return a dict of canonical skill name -> number of times it appears
    in the text. Used for the JD side, since Phase 3b's suggestion
    priority formula needs jd_term_frequency (how often a missing skill
    was emphasized), not just presence/absence.
    """
    doc = _nlp(text)
    matches = _matcher(doc)

    frequencies: Dict[str, int] = {}
    for match_id, start, end in matches:
        match_id_str = _nlp.vocab.strings[match_id]
        canonical_name = _lookup[match_id_str]["name"]
        frequencies[canonical_name] = frequencies.get(canonical_name, 0) + 1

    return frequencies


def get_skill_type(skill_name: str) -> str:
    """
    Look up whether a canonical skill name is 'hard' or 'soft', per the
    taxonomy. Used by Phase 3b's priority formula (is_hard_skill).

    Matching is case-insensitive against the taxonomy's canonical
    names, since callers may not always preserve exact casing.

    Raises ValueError if the skill isn't found in the taxonomy at all —
    silently defaulting an unknown skill's type would let bugs (typos,
    mismatched names) inflate or deflate priority scores unnoticed,
    same reasoning as extract_text_from_pdf's ValueError in Phase 1.
    """
    for skill in _taxonomy:
        if skill["name"].lower() == skill_name.lower():
            return skill["type"]
    raise ValueError(f"Unknown skill: '{skill_name}' not found in taxonomy")
