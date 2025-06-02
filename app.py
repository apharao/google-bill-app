
import streamlit as st
from google.oauth2 import service_account
from google.cloud import vision
import uuid
import re
import os

# Authenticate with Google Cloud Vision using Streamlit secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
)
client = vision.ImageAnnotatorClient(credentials=credentials)

st.set_page_config(page_title="Restaurant Bill Splitter", layout="wide")
st.title("🍽️ Restaurant Bill Splitter with Google OCR")

uploaded_file = st.file_uploader("Upload a receipt image (JPG/PNG)", type=["jpg", "jpeg", "png"])
use_quantities = st.checkbox("Bill includes quantities?", value=True)

def extract_text_from_image(image_bytes):
    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    return texts[0].description if texts else ""

def parse_items(text, use_quantities):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    items = []
    last_description = ""
    debug_output = []

    for line in lines:
        debug_output.append(f"Line: {line}")
        match = re.match(r"^(.*?)(\s+)(-?\d+\.\d{2})$", line)
        if match:
            description = match.group(1).strip()
            price = float(match.group(3))
            if use_quantities:
                qty_price_match = re.match(r"^(.*)\s+\d+\.\d{2}$", description)
                if qty_price_match:
                    description = qty_price_match.group(1).strip()
            item = {"id": str(uuid.uuid4()), "description": description, "price": price}
            items.append(item)
            debug_output.append(f"Matched: {item}")
        else:
            debug_output.append("No match")

    st.session_state.debug_output = debug_output
    return items

if uploaded_file:
    image_bytes = uploaded_file.read()
    extracted_text = extract_text_from_image(image_bytes)
    editable_text = st.text_area("Edit OCR'd text", extracted_text, height=300)
    if st.button("Parse Items"):
        st.session_state.parsed_items = parse_items(editable_text, use_quantities)
        st.success("Parsed items updated.")

if "debug_output" in st.session_state:
    st.subheader("🔍 Debug Log")
    for log in st.session_state.debug_output:
        st.text(log)

if "parsed_items" in st.session_state:
    st.subheader("Parsed Items")
    for item in st.session_state.parsed_items:
        st.write(f"{item['description']} - ${item['price']:.2f}")
