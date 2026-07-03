from src.image_utils import preprocess_image
from src.extract_and_match import extract_and_match

import pytesseract


def process_image_v2(image_path):

    img = preprocess_image(image_path)

    ocr_text = pytesseract.image_to_string(img)

    df = extract_and_match(ocr_text)

    return df