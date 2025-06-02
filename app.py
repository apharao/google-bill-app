
import streamlit as st
from google.cloud import vision
from google.oauth2 import service_account
import json
import uuid

# Load credentials using json.loads on secrets
credentials = service_account.Credentials.from_service_account_info(
    json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
)
client = vision.ImageAnnotatorClient(credentials=credentials)

st.title("📸 Restaurant Bill OCR Parser")
uploaded_file = st.file_uploader("Upload receipt image", type=["png", "jpg", "jpeg"])

quantity_mode = st.checkbox("Does the receipt include quantities?", value=True)

if uploaded_file:
    image_bytes = uploaded_file.read()
    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)
    text = response.text_annotations[0].description if response.text_annotations else ""

    st.text_area("Extracted Text", value=text, height=300)

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    items = []
    i = 0

    while i < len(lines):
        desc = lines[i]
        qty = None
        price = None
        try:
            if quantity_mode and i + 2 < len(lines):
                qty_candidate = float(lines[i+1])
                price_candidate = float(lines[i+2])
                qty = qty_candidate
                price = price_candidate
                i += 3
            elif i + 1 < len(lines):
                price_candidate = float(lines[i+1])
                price = price_candidate
                i += 2
            else:
                i += 1
                continue
            items.append({
                "id": str(uuid.uuid4()),
                "description": desc,
                "price": price
            })
        except ValueError:
            i += 1

    st.subheader("Parsed Items")
    if not items:
        st.write("⚠️ No items could be parsed.")
    for item in items:
        st.write(f"{item['description']} - ${item['price']:.2f}")
