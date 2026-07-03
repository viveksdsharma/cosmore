import streamlit as st
import tempfile
import os

from src.ocr_processor_v2 import process_image_v2

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Ingredient Scanner",
    page_icon="🧴",
    layout="wide"
)

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🧴 Ingredient Scanner")

st.markdown("---")

st.write(
    "Upload a cosmetic product label and recover ingredients using OCR + fuzzy matching."
)

# --------------------------------------------------
# FILE UPLOAD
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload Product Label",
    type=["png", "jpg", "jpeg"]
)

# --------------------------------------------------
# SCAN BUTTON
# --------------------------------------------------

if uploaded_file is not None:

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:

        tmp.write(uploaded_file.read())

        temp_path = tmp.name

    if st.button("Scan Ingredients"):

        with st.spinner("Scanning image..."):

            df = process_image_v2(temp_path)

        # ------------------------------------------
        # DISPLAY DATAFRAME
        # ------------------------------------------

        display_df = df[
            [
                "Matched Name",
                "Rating",
                "Description",
                "Score"
            ]
        ].sort_values(
            by="Score",
            ascending=False
        )

        # ------------------------------------------
        # RATING EMOJIS
        # ------------------------------------------

        rating_map = {
            "best": "🟢 Best",
            "good": "🟡 Good",
            "average": "🟠 Average",
            "poor": "🔴 Poor",
            "not rated": "⚪ Not Rated"
        }

        display_df["Rating"] = (
            display_df["Rating"]
            .fillna("not rated")
            .str.lower()
            .map(rating_map)
        )

        # ------------------------------------------
        # SUCCESS MESSAGE
        # ------------------------------------------

        st.success(f"Recovered {len(display_df)} ingredients")

        # ------------------------------------------
        # METRICS
        # ------------------------------------------

        best_count = len(
            display_df[
                display_df["Rating"].str.contains("Best", na=False)
            ]
        )

        good_count = len(
            display_df[
                display_df["Rating"].str.contains("Good", na=False)
            ]
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Ingredients",
            len(display_df)
        )

        col2.metric(
            "Best Rated",
            best_count
        )

        col3.metric(
            "Good Rated",
            good_count
        )

        st.markdown("---")

        # ------------------------------------------
        # TOP INGREDIENTS
        # ------------------------------------------

        st.subheader("⭐ Top Ingredients")

        for _, row in display_df.head(5).iterrows():

            st.write(
                f"**{row['Matched Name']}** — {row['Rating']}"
            )

        st.markdown("---")

        # ------------------------------------------
        # FULL RESULTS
        # ------------------------------------------

        st.subheader("📋 Full Results")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        # ------------------------------------------
        # CLEANUP
        # ------------------------------------------

        os.unlink(temp_path)