"""
Tests for backend/services/embedding.py — compute_similarity and
compute_match_score.

compute_similarity() is tested loosely (ordering/relative checks only) —
exact cosine values depend on the embedding model itself, which we treat
as a black box here. compute_match_score() is tested more strictly since
its normalization logic (FLOOR/CEILING clamping) is our own code and
fully deterministic given a raw similarity value.
"""
from backend.services.embedding import compute_similarity, compute_match_score


def test_similar_texts_score_higher_than_unrelated_texts():
    resume = "Experienced Python developer skilled in machine learning and FastAPI."
    jd_related = "Looking for a Python developer with machine learning experience."
    jd_unrelated = "The chef prepares fresh pasta daily using traditional Italian techniques."

    related_score = compute_match_score(resume, jd_related)
    unrelated_score = compute_match_score(resume, jd_unrelated)

    assert related_score > unrelated_score


def test_score_is_always_within_0_to_100():
    # Even for a near-identical pair (raw cosine close to 1.0, well above
    # CEILING) the score must clamp to 100, not exceed it.
    resume = "Python developer with machine learning and FastAPI experience."
    jd_identical = "Python developer with machine learning and FastAPI experience."

    score = compute_match_score(resume, jd_identical)

    assert 0 <= score <= 100


def test_completely_unrelated_text_scores_near_zero():
    # Raw cosine for genuinely unrelated text sits at/below FLOOR, so the
    # score should land near the bottom of the scale. We assert "low",
    # not "exactly 0" — exact value depends on current FLOOR/CEILING
    # calibration (see calibration/), which is expected to be refined
    # over time as more labeled data is added.
    resume = "Experienced Python developer skilled in machine learning and FastAPI."
    jd_unrelated = "The chef prepares fresh pasta daily using traditional Italian techniques."

    score = compute_match_score(resume, jd_unrelated)

    assert score <= 5


def test_score_return_type_is_int_not_float():
    resume = "Python developer with FastAPI experience."
    jd = "Looking for a Python developer."

    score = compute_match_score(resume, jd)

    assert isinstance(score, int)


def test_compute_similarity_returns_a_float_between_negative_one_and_one():
    # Cosine similarity is mathematically bounded to [-1, 1]; in practice
    # for real text it stays positive, but we assert the theoretical bound
    # rather than a narrower empirical range here.
    resume = "Python developer with FastAPI experience."
    jd = "Looking for a Python developer."

    similarity = compute_similarity(resume, jd)

    assert isinstance(similarity, float)
    assert -1.0 <= similarity <= 1.0
