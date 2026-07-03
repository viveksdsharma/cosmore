import pandas as pd


# ---------------------------------------
# Ingredient Family Rules
# ---------------------------------------

RULES = {

    "Silicone": [
        "methicone",
        "siloxane",
        "silicone"
    ],

    "Humectant": [
        "glycol",
        "glycerin",
        "glycerine",
        "hyaluron",
        "urea",
        "xylitol",
        "panthenol"
    ],

    "Alcohol": [
        "alcohol"
    ],

    "Oil": [
        "oil"
    ],

    "Butter": [
        "butter"
    ],

    "Wax": [
        "wax",
        "beeswax",
        "cera"
    ],

    "PEG": [
        "peg"
    ],

    "Surfactant": [
        "polysorbate",
        "stearate",
        "laureth",
        "sulfate",
        "sarcosinate"
    ],

    "Peptide": [
        "peptide"
    ],

    "Botanical Extract": [
        "extract"
    ],

    "Vitamin": [
        "tocopherol",
        "ascorb",
        "niacinamide",
        "retinol",
        "vitamin"
    ],

    "Preservative": [
        "phenoxyethanol",
        "paraben",
        "benzoate",
        "sorbate",
        "ethylhexylglycerin"
    ],

    "Fragrance": [
        "parfum",
        "fragrance",
        "limonene",
        "citral",
        "linalool"
    ]
}


# ---------------------------------------
# Classifier
# ---------------------------------------

def classify_family(name):

    name = str(name).lower()

    for family, keywords in RULES.items():

        for word in keywords:

            if word in name:

                return family

    return "Other"


# ---------------------------------------
# Enrich Database
# ---------------------------------------

def enrich_database(input_csv,
                    output_csv):

    df = pd.read_csv(input_csv)

    df["Family"] = df["Name"].apply(classify_family)

    df.to_csv(output_csv,
              index=False)

    print("Database enriched.")

    print(df["Family"].value_counts())

    return df


if __name__ == "__main__":

    enrich_database(
        "../paulaschoice_us_ingredients_clean.csv",
        "../paulaschoice_us_ingredients_enriched.csv"
    )