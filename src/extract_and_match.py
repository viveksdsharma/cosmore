# src/extract_and_match.py

import pandas as pd
from .ingredient_extractor import extract_ingredient_candidates
from .fuzzy_matcher import match_ingredient


def extract_and_match_from_text(ocr_text, threshold=80):
    """
    Full text pipeline:
    raw OCR text -> ingredient candidates -> fuzzy matching
    """
    candidates = extract_ingredient_candidates(ocr_text)

    results = []
    for ing in candidates:
        res = match_ingredient(ing, threshold=threshold)
        results.append(res)

    df = pd.DataFrame(results)

    # If match_ingredient returns full metadata, keep all columns.
    # Otherwise still return whatever exists.
    return df


def extract_candidates_only(ocr_text):
    """
    Utility function for debugging extraction only.
    """
    return extract_ingredient_candidates(ocr_text)