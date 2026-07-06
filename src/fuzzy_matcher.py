# src/fuzzy_matcher.py

import re
import pandas as pd
from rapidfuzz import process, fuzz
from .ingredient_db import load_ingredient_db, get_known_terms

# ---------------------------
# Load ingredient DB once
# ---------------------------
db = load_ingredient_db()
db["Name_clean"] = db["Name"].astype(str).str.lower().str.strip()
known_terms = get_known_terms(db)


# ---------------------------
# Helper cleaning
# ---------------------------
def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()

    # basic OCR cleanup
    text = text.replace("/", " ")
    text = text.replace("\\", " ")
    text = re.sub(r"[^a-z0-9\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def generate_match_variants(text: str):
    """
    Generate extra candidate variants for fuzzy matching.
    This is where we recover difficult OCR fragments.
    """
    text = normalize_text(text)
    variants = {text}

    # ---------------------------
    # Generic cleanup
    # ---------------------------
    # remove leading filler words
    text2 = re.sub(r"^(and|tand|rate|nel|land)\s+", "", text).strip()
    if text2:
        variants.add(text2)

    # remove trailing junk fillers
    text3 = re.sub(r"\b(and|tand|nel|land)\b", " ", text)
    text3 = re.sub(r"\s+", " ", text3).strip()
    if text3:
        variants.add(text3)

    # ---------------------------
    # PEG stearate family
    # ---------------------------
    if "peg" in text and "stearate" in text:
        variants.add("peg stearate")

        m = re.search(r"peg\s*(\d+)\s*stearate", text)
        if m:
            num = m.group(1)
            variants.add(f"peg-{num} stearate")
            variants.add(f"peg {num} stearate")

        # common OCR confusion for PEG-100 Stearate
        if "109" in text:
            variants.add("peg-100 stearate")
            variants.add("peg 100 stearate")

    # ---------------------------
    # peptide family
    # ---------------------------
    if "tetrapeptide" in text or "peptide" in text:
        variants.add("tetrapeptide-7")
        variants.add("palmitoyl tetrapeptide-7")

        # if palmitoyl exists anywhere, prioritize peptide variant
        if "palmitoyl" in text:
            variants.add("palmitoyl tetrapeptide-7")

    # ---------------------------
    # caprylic / triglyceride family
    # ---------------------------
    if "caprylic" in text:
        variants.add("caprylic")
        variants.add("caprylic triglyceride")
        variants.add("caprylic capric triglyceride")
        variants.add("caprylic/capric triglyceride")

    # ---------------------------
    # cetearyl family
    # ---------------------------
    if "cetearyl" in text:
        variants.add("cetearyl alcohol")

    # ---------------------------
    # rubus oil family
    # ---------------------------
    if "rubus" in text and "oil" in text:
        variants.add("rubus oil")
        variants.add("seed oil")

    # ---------------------------
    # extract family
    # ---------------------------
    if "fragaria ananassa" in text:
        variants.add("fragaria ananassa fruit extract")
        variants.add("fragaria ananassa extract")

    # remove ultra-short garbage
    final_variants = []
    for v in variants:
        v = normalize_text(v)
        if len(v) >= 4:
            final_variants.append(v)

    # preserve order-ish while deduplicating
    seen = set()
    deduped = []
    for v in final_variants:
        if v not in seen:
            seen.add(v)
            deduped.append(v)

    return deduped


# ---------------------------
# Matching functions
# ---------------------------
def best_match_across_variants(candidate: str, threshold=80):
    """
    Try multiple fuzzy strategies across multiple generated variants.
    Returns best match dict or None.
    """
    variants = generate_match_variants(candidate)
    best = None

    # We'll compare against Name_clean
    choices = db["Name_clean"].tolist()

    scorers = [
        ("token_sort", fuzz.token_sort_ratio),
        ("token_set", fuzz.token_set_ratio),
        ("partial", fuzz.partial_ratio),
    ]

    for variant in variants:
        for scorer_name, scorer in scorers:
            match = process.extractOne(variant, choices, scorer=scorer)
            if not match:
                continue

            matched_name_clean, score, _ = match

            if best is None or score > best["Score"]:
                best = {
                    "Variant": variant,
                    "Matched Name Clean": matched_name_clean,
                    "Score": score,
                    "Scorer": scorer_name
                }

    if best and best["Score"] >= threshold:
        return best
    return best  # return best anyway so we can inspect score


def match_ingredient(ingredient, threshold=80):
    """
    Match one ingredient candidate to DB with smarter fallback.
    """
    ingredient_clean = normalize_text(ingredient)
    best = best_match_across_variants(ingredient_clean, threshold=threshold)

    if best and best["Matched Name Clean"] is not None:
        matched_clean = best["Matched Name Clean"]
        row = db[db["Name_clean"] == matched_clean].iloc[0]

        if best["Score"] >= threshold:
            return {
                "Input": ingredient,
                "Matched Name": row["Name"],
                "Description": row.get("Description"),
                "Rating": row.get("Rating"),
                "Family": row.get("Family"),
                "Synonyms": row.get("Synonyms"),
                "Score": best["Score"]
            }

    # fallback if below threshold or no match
    return {
        "Input": ingredient,
        "Matched Name": None,
        "Description": None,
        "Rating": None,
        "Family": None,
        "Synonyms": None,
        "Score": best["Score"] if best else 0
    }


def bulk_process(ingredient_list, threshold=80, unmatched_log='unmatched_ingredients.csv'):
    """
    Match a list of extracted ingredient candidates.
    """
    results = []
    unmatched = []

    for ing in ingredient_list:
        res = match_ingredient(ing, threshold)
        results.append(res)

        if res["Matched Name"] is None:
            unmatched.append(res)

    df = pd.DataFrame(results)

    if unmatched:
        pd.DataFrame(unmatched).to_csv(
            unmatched_log,
            mode='a',
            index=False,
            header=not pd.io.common.file_exists(unmatched_log)
        )
        print(f"⚠️ Logged {len(unmatched)} unmatched ingredients to '{unmatched_log}'")

    return df