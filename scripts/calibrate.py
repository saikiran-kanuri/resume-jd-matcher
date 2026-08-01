"""
scripts/calibrate.py

Calibration script for Phase 3a score normalization.
Reads labeled JD calibration pairs, computes raw cosine similarity
against the reference resume, and prints results sorted by similarity
so poor/medium/good boundaries can be identified manually.

This is a throwaway diagnostic script, not part of the production pipeline.
"""

import csv
import sys
from pathlib import Path

# Make backend/ importable when running this script directly
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.services.embedding import compute_similarity
from backend.services.pdf_parser import extract_text_from_pdf

RESUME_PATH = Path.home() / "Desktop" / "Sai_Kiran_Kanuri_Resume_Final.pdf"
CALIBRATION_DIR = Path(__file__).resolve().parent.parent / "calibration"
LABELS_CSV = CALIBRATION_DIR / "labels.csv"


def load_labels() -> list[dict]:
    with open(LABELS_CSV, newline="") as f:
        return list(csv.DictReader(f))


def main():
    resume_text = extract_text_from_pdf(str(RESUME_PATH))

    rows = load_labels()
    results = []

    for row in rows:
        jd_path = CALIBRATION_DIR / row["filename"]
        jd_text = jd_path.read_text()

        raw_cosine = compute_similarity(resume_text, jd_text)
        results.append({
            "filename": row["filename"],
            "label": row["label"],
            "raw_cosine": raw_cosine,
        })

    results.sort(key=lambda r: r["raw_cosine"])

    print(f"{'filename':<20} {'label':<8} {'raw_cosine':>10}")
    print("-" * 40)
    for r in results:
        print(f"{r['filename']:<20} {r['label']:<8} {r['raw_cosine']:>10.3f}")


if __name__ == "__main__":
    main()