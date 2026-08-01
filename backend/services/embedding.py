"""
embedding.py

Generates sentence embeddings and computes a resume-JD match score using
cosine similarity.

Design notes:
- The sentence-transformers model is loaded ONCE at module import time,
  same "load once, not per-request" principle used in skill_extraction.py
  and pdf_parser.py. Loading all-MiniLM-L6-v2 involves reading ~80MB of
  weights from disk; doing that per-request would make every API call
  slow for no reason.
- compute_similarity() returns the RAW cosine similarity, unmodified.
  compute_match_score() is the public-facing function that normalizes
  it into a 0-100 integer score.
- NORMALIZATION IS A PLACEHOLDER (see module-level constants below).
  Per Project Doc Section 3a, real calibration happens after this
  pipeline exists: label ~15-20 resume-JD pairs as good/medium/poor fit,
  observe what raw cosine scores they actually produce with this model,
  then replace SIMILARITY_FLOOR / SIMILARITY_CEILING with real numbers.
  Do not treat these constants as final.
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

_model = SentenceTransformer("all-MiniLM-L6-v2")

SIMILARITY_FLOOR = 0.18    # calibrated from 22-pair labeled set (poor/medium boundary), see calibration/
SIMILARITY_CEILING = 0.50  # calibrated from 22-pair labeled set (~above good-label mean), see calibration/


def get_embedding(text: str) -> np.ndarray:
    """
    Encode a single piece of text into its sentence embedding vector.
    """
    return _model.encode(text)


def compute_similarity(resume_text: str, jd_text: str) -> float:
    """
    Return the RAW cosine similarity between resume and JD embeddings,
    unmodified (theoretically -1 to 1, in practice usually 0.0-0.8 for
    real English text with this model).
    """
    resume_embedding = get_embedding(resume_text)
    jd_embedding = get_embedding(jd_text)

    similarity_matrix = cosine_similarity(
        resume_embedding.reshape(1, -1),
        jd_embedding.reshape(1, -1),
    )
    return float(similarity_matrix[0][0])


def compute_match_score(resume_text: str, jd_text: str) -> int:
    """
    Return a 0-100 integer match score between resume and JD text.

    Normalization is currently a PLACEHOLDER linear stretch between
    SIMILARITY_FLOOR and SIMILARITY_CEILING, clamped to [0, 100].
    This will be replaced once real calibration data exists.
    """
    raw_similarity = compute_similarity(resume_text, jd_text)

    stretched = (raw_similarity - SIMILARITY_FLOOR) / (
        SIMILARITY_CEILING - SIMILARITY_FLOOR
    )
    score = stretched * 100

    score = max(0.0, min(100.0, score))

    return round(score)
