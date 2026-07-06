from src.image_utils import preprocess_image
from src.extract_and_match import extract_and_match_from_text

import pytesseract


def process_image_v2(image_path):

    # Preprocess image
    img = preprocess_image(image_path)

    # OCR
    ocr_text = pytesseract.image_to_string(img)

    # Extract + Match
    df = extract_and_match_from_text(ocr_text)

    return df