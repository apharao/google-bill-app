import streamlit as st
import json
from google.oauth2 import service_account
from google.cloud import vision
import uuid

# Authenticate with Google Cloud
credentials = service_account.Credentials.from_service_account_info(
    json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
)
client = vision.ImageAnnotatorClient(credentials=credentials)

st.title("📸 Restaurant Receipt Splitter")

uploaded_file = st.file_uploader("Upload a receipt image", type=["png", "jpg", "jpeg"])

def perform_ocr(image_bytes):
    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)
    return response.text_annotations[0].description if response.text_annotations else ""

def parse_items(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    parsed = []

    for i, line in enumerate(lines):
        words = line.split()
        price = None
        for w in reversed(words):
            try:
                price_val = float(w.replace("$", "").replace(",", ""))
                if 0 < price_val < 1000:
                    price = price_val
                    break
            except:
                continue
        if price is not None:
            description = line.replace(str(price), "").strip(" -$")
            parsed.append({"id": str(uuid.uuid4()), "description": description, "price": price})
    return parsed

if uploaded_file:
    image_bytes = uploaded_file.read()
    ocr_text = perform_ocr(image_bytes)
    st.subheader("OCR Text")
    editable_text = st.text_area("Edit OCR Text", ocr_text, height=300)

    if st.button("Parse Items"):
        st.session_state.parsed_items = parse_items(editable_text)
        st.success("Parsed items updated.")

    if "parsed_items" in st.session_state:
        st.subheader("Parsed Items")
        for item in st.session_state.parsed_items:
            st.write(f"{item['description']} - ${item['price']:.2f}")