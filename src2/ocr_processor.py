### src/ocr_processor.py
import pytesseract
import pandas as pd
from rapidfuzz import process, fuzz
from .image_utils import preprocess_image
from .fuzzy_matcher import match_ingredient

def extract_ingredients(text):
    """Parse OCR text to clean list of ingredient strings."""
    lines = text.split(',')  # Split on commas
    cleaned = []
    for line in lines:
        line = line.lower().strip()
        line = line.replace('(and)', '').replace('[and]', '')
        line = line.replace('-', '')
        line = line.replace('ingredients:', '')
        line = line.strip()
        if line:
            cleaned.append(line)
    return cleaned


def process_image(image_path, threshold=80):
    """Full pipeline: Image -> Text -> Ingredient Matching."""
    img = preprocess_image(image_path)
    ocr_text = pytesseract.image_to_string(img)
    ingredients = extract_ingredients(ocr_text)

    results = [match_ingredient(ing, threshold) for ing in ingredients]
    df_results = pd.DataFrame(results)

    unmatched = df_results[df_results['Matched Name'].isna()]
    if not unmatched.empty:
        unmatched.to_csv("unmatched_ingredients.csv", mode='a', index=False, header=False)
        print(f"⚠️ Logged {len(unmatched)} unmatched ingredients to 'unmatched_ingredients.csv'")

    return df_results