
import pandas as pd

def load_ingredient_db(path='paulaschoice_us_ingredients_clean.csv'):
    return pd.read_csv(path)

def get_known_terms(db):
    names = set(db['Name'].str.lower())
    return list(names)
