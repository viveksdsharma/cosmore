
import pandas as pd

def load_ingredient_db(path='paulaschoice_us_ingredients_clean.csv'):
    """Load the cleaned ingredient database."""
    df = pd.read_csv(path)
    return df

def get_known_terms(db):
    """Extract known ingredient names from database."""
    known_terms = set(db['Name'].str.lower())
    return list(known_terms)
