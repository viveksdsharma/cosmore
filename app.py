# app.py
"""
Ingredient Scanner v2
Features
- Upload image
- Camera capture
- Paste ingredient list
- OCR + Fuzzy Matching
"""

import os
import tempfile
import streamlit as st

from src.ocr_processor_v2 import process_image_v2
from src.extract_and_match import extract_and_match_from_text

st.set_page_config(page_title="Ingredient Scanner",
                   page_icon="🧴",
                   layout="wide")

st.title("🧴 Ingredient Scanner")
st.write("Choose one input method below.")

method = st.radio(
    "Input Method",
    ["📁 Upload Image", "📷 Take Photo", "📝 Paste Ingredients"],
    horizontal=True,
)

uploaded_file = None
camera_image = None
ingredient_text = ""

st.markdown("---")

if method == "📁 Upload Image":
    uploaded_file = st.file_uploader(
        "Upload ingredient label",
        type=["png", "jpg", "jpeg"]
    )

elif method == "📷 Take Photo":
    camera_image = st.camera_input(
        "Take a photo of the ingredient label"
    )

else:
    ingredient_text = st.text_area(
        "Paste ingredient list",
        height=220,
        placeholder="Water, Glycerin, Niacinamide..."
    )

scan = st.button(
    "🔍 Scan Ingredients",
    use_container_width=True,
    type="primary"
)

if scan:

    if (
        uploaded_file is None
        and camera_image is None
        and ingredient_text.strip() == ""
    ):
        st.warning("Please provide an image or ingredient list.")
        st.stop()

    temp_path = None

    with st.spinner("Scanning..."):

        if ingredient_text.strip():
            df = extract_and_match_from_text(
                ingredient_text
            )

        else:

            if camera_image is not None:

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".png"
                ) as tmp:

                    tmp.write(camera_image.read())
                    temp_path = tmp.name

            else:

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".png"
                ) as tmp:

                    tmp.write(uploaded_file.read())
                    temp_path = tmp.name

            df = process_image_v2(temp_path)

    if temp_path and os.path.exists(temp_path):
        os.unlink(temp_path)

    if df.empty:
        st.error("No ingredients detected.")
        st.stop()

    display_df = df[
        [
            "Matched Name",
            "Family",
            "Rating",
            "Description",
            "Score",
        ]
    ].copy()

    display_df = display_df.dropna(subset=["Matched Name"])
    display_df = display_df.drop_duplicates(
        subset=["Matched Name"]
    )

    display_df["Score"] = (
        display_df["Score"]
        .fillna(0)
        .round(1)
    )

    rating_map = {
        "best": "🟢 Best",
        "good": "🟡 Good",
        "average": "🟠 Average",
        "poor": "🔴 Poor",
    }

    display_df["Rating"] = (
        display_df["Rating"]
        .fillna("Not Rated")
        .astype(str)
        .str.lower()
        .map(rating_map)
        .fillna("⚪ Not Rated")
    )

    best = display_df["Rating"].str.contains("Best", na=False).sum()
    good = display_df["Rating"].str.contains("Good", na=False).sum()

    score = max(
        0,
        100
        - display_df["Rating"].str.contains("Poor", na=False).sum() * 12
        - display_df["Rating"].str.contains("Average", na=False).sum() * 5
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingredients", len(display_df))
    c2.metric("Best Rated", int(best))
    c3.metric("Good Rated", int(good))
    c4.metric("Overall Score", f"{score}/100")

    st.markdown("---")
    st.subheader("🤖 AI Product Summary")

    family_counts = (
        display_df["Family"]
        .fillna("Other")
        .value_counts()
    )

    if best >= 5:
        st.success("🟢 Rich in highly-rated ingredients.")
    elif best >= 2:
        st.success("🟡 Contains several beneficial ingredients.")
    else:
        st.warning("Limited number of highly-rated ingredients.")

    if family_counts.get("Humectant", 0):
        st.success("💧 Hydration-supporting ingredients detected.")

    if family_counts.get("Silicone", 0):
        st.info("✨ Silicone-based formulation.")

    if family_counts.get("Fragrance", 0) == 0:
        st.success("✅ No fragrance ingredients detected.")

    st.markdown("---")
    st.subheader("🧬 Ingredient Family Distribution")
    st.bar_chart(family_counts)

    st.markdown("---")
    st.subheader("⭐ Top Ingredients")

    for _, row in display_df.head(5).iterrows():
        with st.container():
            st.markdown(f"### {row['Matched Name']}")
            st.write(f"**Family:** {row['Family']}")
            st.write(f"**Rating:** {row['Rating']}")
            st.write(str(row["Description"])[:220])
            st.markdown("---")

    st.download_button(
        "📥 Download Results",
        display_df.to_csv(index=False),
        "ingredient_scan_results.csv",
        "text/csv"
    )

    st.markdown("---")
    st.subheader("📋 Full Results")
    st.dataframe(display_df, use_container_width=True, hide_index=True)
