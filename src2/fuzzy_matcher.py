### src/fuzzy_matcher.py

from rapidfuzz import process, fuzz
from ingredient_db import load_ingredient_db, get_known_terms
import pandas as pd

db = load_ingredient_db()
known_terms = get_known_terms(db)


def clean_text(text):
    """Basic cleaning: lowercase, strip, remove brackets."""
    import re
    text = text.lower().strip()
    text = re.sub(r"[\[\]\(\)]", "", text)
    return text


def auto_correct_ocr(ocr_text, threshold=80):
    """Correct OCR output based on known ingredient terms."""
    cleaned = clean_text(ocr_text)
    match = process.extractOne(cleaned, known_terms, scorer=fuzz.token_sort_ratio)
    if match and match[1] >= threshold:
        return match[0]
    return cleaned


def match_ingredient(ingredient, threshold=80):
    """Fuzzy match corrected ingredient to database."""
    corrected = auto_correct_ocr(ingredient, threshold)
    match = process.extractOne(corrected, db["Name"], scorer=fuzz.token_sort_ratio)
    if match and match[1] >= threshold:
        db_row = db[db["Name"] == match[0]].iloc[0]
        return {
            "Input": ingredient,
            "Corrected": corrected,
            "Matched Name": db_row["Name"],
            "Description": db_row["Description"],
            "Rating": db_row["Rating"],
            "Score": match[1],
        }
    else:
        return {
            "Input": ingredient,
            "Corrected": corrected,
            "Matched Name": None,
            "Description": None,
            "Rating": None,
            "Score": match[1] if match else None,
        }


def bulk_process(ingredient_list, threshold=80, unmatched_log="unmatched_ingredients.csv"):
    """Process list of ingredients, return DataFrame, log unmatched."""
    results = []
    unmatched = []

    for ing in ingredient_list:
        res = match_ingredient(ing, threshold)
        results.append(res)
        if res["Matched Name"] is None:
            unmatched.append(res)

    if unmatched:
        df_unmatched = pd.DataFrame(unmatched)
        df_unmatched.to_csv(unmatched_log, mode="a", index=False, header=False)
        print(f"⚠️ Logged {len(unmatched)} unmatched ingredients to '{unmatched_log}'")

    return pd.DataFrame(results)
