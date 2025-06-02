
import streamlit as st
import re
import uuid

st.set_page_config(page_title="Receipt Parser", layout="centered")

def parse_ocr_text(text, includes_quantity):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    items = []
    i = 0

    while i < len(lines):
        desc = lines[i]
        if i + 2 < len(lines) and re.match(r"^-?\d+\.\d{2}$", lines[i+1]) and re.match(r"^-?\d+\.\d{2}$", lines[i+2]):
            # Case: description + quantity + price
            price = float(lines[i+2])
            i += 3
        elif i + 1 < len(lines) and re.match(r"^-?\d+\.\d{2}$", lines[i+1]):
            # Case: description + price (no quantity)
            price = float(lines[i+1])
            i += 2
        else:
            i += 1
            continue

        items.append({
            "id": str(uuid.uuid4()),
            "description": desc,
            "price": price
        })
    return items

st.title("🧾 Receipt OCR Parser")

editable_text = st.text_area("Paste or Edit OCR Text:", height=300)

includes_quantity = st.checkbox("This receipt includes quantities")

if st.button("Parse Items"):
    st.session_state.parsed_items = parse_ocr_text(editable_text, includes_quantity)
    st.success("Parsed items updated.")

if "parsed_items" in st.session_state:
    st.subheader("Parsed Items")
    for item in st.session_state.parsed_items:
        st.markdown(f"- **{item['description']}** - ${item['price']:.2f}")
