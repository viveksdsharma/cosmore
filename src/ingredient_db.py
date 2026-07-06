import pandas as pd
from pathlib import Path


def load_ingredient_db(path=None):

    if path is None:
        path = Path(__file__).resolve().parent.parent / "data" / "paulaschoice_us_ingredients_enriched.csv"

    return pd.read_csv(path)


def get_known_terms(db):

    names = set(
        db["Name"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    return list(names)