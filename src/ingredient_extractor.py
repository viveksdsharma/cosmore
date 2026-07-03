# src/ingredient_extractor.py

import re

STOPWORDS = {
    "ingredients", "ingredient", "contains", "may contain",
    "and", "or", "with", "the"
}

JUNK_TOKENS = {
    "fp", "ee", "eo", "=", "<", ">", ".", ",", "-", "_"
}

# Ingredient-like anchor words that help us split giant OCR chunks
ANCHOR_WORDS = [
    "aqua", "agua", "water",
    "glycol", "glycerin", "glycerine",
    "dimethicone", "siloxane", "alcohol",
    "stearate", "butter", "extract", "oil",
    "hyaluronate", "panthenol", "polysorbate",
    "peptide", "tetrapeptide", "copolymer"
]


def normalize_ocr_text(text: str) -> str:
    """
    Clean raw OCR text before ingredient extraction.
    """
    if not isinstance(text, str):
        return ""

    text = text.lower()

    # Remove ingredient prefix variants like "ingredients:" / "ingredient"
    text = re.sub(r"\b[a-z]*ingredients?\b[:\s-]*", " ", text)

    # Join hyphenated line breaks
    text = re.sub(r"-\s*\n\s*", "", text)

    # Convert newlines/tabs to spaces
    text = text.replace("\n", " ").replace("\t", " ")

    # Remove brackets
    text = re.sub(r"[\[\]\(\)\{\}]", " ", text)

    # Replace slash, backslash, pipes
    text = text.replace("/", " ").replace("\\", " ").replace("|", " ")

    # Replace weird dashes
    text = re.sub(r"[–—_]", " ", text)

    # Remove special characters except comma/hyphen
    text = re.sub(r"[^a-z0-9,\-\s]", " ", text)

    # Collapse spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def repair_common_ocr_phrases(candidate: str) -> str:
    """
    Light phrase-level OCR repair rules.
    These are intentionally heuristic.
    """
    if not candidate:
        return ""

    c = candidate

    # Common OCR weirdness
    c = c.replace("ext act", "extract")
    c = c.replace("ext act", "extract")
    c = c.replace("poiysarbate", "polysorbate")
    c = c.replace("a lysorbate", "polysorbate")
    c = c.replace("gord oil", "seed oil")

    # common "fetrapeptide" OCR typo
    c = c.replace("fetrapeptide", "tetrapeptide")

    # trim duplicate spaces
    c = re.sub(r"\s+", " ", c).strip()

    return c


def clean_candidate(candidate: str) -> str:
    """
    Clean an individual extracted ingredient candidate.
    """
    if not isinstance(candidate, str):
        return ""

    candidate = candidate.lower().strip()

    # Remove leading/trailing punctuation
    candidate = candidate.strip(" ,.-_")

    # Remove leading numbers like "3 butter"
    candidate = re.sub(r"^\d+\s+", "", candidate)

    # Remove standalone 'and'
    candidate = re.sub(r"\band\b", " ", candidate)

    # Collapse spaces
    candidate = re.sub(r"\s+", " ", candidate).strip()

    # Repair OCR phrase artifacts
    candidate = repair_common_ocr_phrases(candidate)

    if candidate in STOPWORDS or candidate in JUNK_TOKENS:
        return ""

    return candidate


def is_likely_ingredient(candidate: str) -> bool:
    """
    Heuristic filter for ingredient-like candidates.
    """
    if not candidate:
        return False

    if len(candidate) < 4:
        return False

    if re.fullmatch(r"\d+", candidate):
        return False

    if candidate in JUNK_TOKENS:
        return False

    if not re.search(r"[a-z]", candidate):
        return False

    # Allow common short ingredient words
    safe_short_words = {"agua", "aqua", "water", "butter", "oil"}
    if len(candidate.split()) == 1 and len(candidate) <= 4 and candidate not in safe_short_words:
        return False

    return True


def split_large_chunk(chunk: str):
    """
    Split giant OCR chunks into smaller candidate pieces using anchor words.
    Example:
    'butylene glycol nel land poiysarbate 20 tand palmitoyl ...'
    should yield smaller pieces around glycol / polysorbate / peptide.
    """
    chunk = chunk.strip()
    if not chunk:
        return []

    # If chunk is already small enough, keep it
    if len(chunk.split()) <= 5:
        return [chunk]

    words = chunk.split()
    segments = []
    current = []

    for word in words:
        current.append(word)

        # if word contains an anchor, close current segment
        if any(anchor in word for anchor in ANCHOR_WORDS):
            segments.append(" ".join(current).strip())
            current = []

    # leftover words
    if current:
        segments.append(" ".join(current).strip())

    # Also keep the full chunk because sometimes fuzzy matching still works on full phrase
    results = [chunk]

    # Add segments that are meaningful
    for seg in segments:
        seg = seg.strip()
        if seg and seg != chunk:
            results.append(seg)

    return results


def generate_sub_candidates(candidate: str):
    """
    Generate extra sub-candidates from a cleaned candidate.
    This helps when one OCR chunk actually contains multiple ingredients.
    """
    out = [candidate]

    # If candidate contains "polysorbate", create a focused sub-candidate around it
    m = re.search(r"(polysorbate\s*\d+)", candidate)
    if m:
        out.append(m.group(1).strip())

    # If candidate contains "butylene glycol"
    if "butylene glycol" in candidate:
        out.append("butylene glycol")

    # If candidate contains "panthenol"
    if "panthenol" in candidate:
        out.append("panthenol")

    # sodium hyaluronate
    if "sodium hyaluronate" in candidate:
        out.append("sodium hyaluronate")

    # botanical extract ending
    if "fragaria ananassa" in candidate:
        out.append(candidate.replace("tier it", "").replace("ext act", "extract").strip())
        out.append("fragaria ananassa extract")

    # berry oil pattern
    if "rubus" in candidate and "oil" in candidate:
        out.append(candidate)
        out.append("rubus seed oil")

    # peptide chunk
    if "tetrapeptide" in candidate or "peptide" in candidate:
        peptide_part = re.search(r"([a-z0-9\s\-]*tetrapeptide\-?\d*)", candidate)
        if peptide_part:
            out.append(peptide_part.group(1).strip())

    return [x for x in out if x]


def extract_ingredient_candidates(ocr_text: str):
    """
    Main extraction pipeline:
    raw OCR text -> cleaned candidate list
    """
    text = normalize_ocr_text(ocr_text)

    # Split first on commas
    rough_parts = [part.strip() for part in text.split(",") if part.strip()]

    all_candidates = []

    for part in rough_parts:
        # Step 1: clean the raw chunk
        part = clean_candidate(part)
        if not part:
            continue

        # Step 2: split large chunk into smaller segments
        subparts = split_large_chunk(part)

        for sub in subparts:
            sub = clean_candidate(sub)
            if not sub:
                continue

            # Step 3: generate extra focused sub-candidates
            generated = generate_sub_candidates(sub)

            for g in generated:
                g = clean_candidate(g)
                if is_likely_ingredient(g):
                    all_candidates.append(g)

    # Deduplicate while preserving order
    seen = set()
    final_candidates = []
    for c in all_candidates:
        if c not in seen:
            seen.add(c)
            final_candidates.append(c)

    return final_candidates