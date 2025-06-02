import streamlit as st
import os
import json
from google.oauth2 import service_account
from google.cloud import vision
import uuid

# Load credentials from JSON string in Streamlit secrets
credentials = service_account.Credentials.from_service_account_info(
    json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
)

client = vision.ImageAnnotatorClient(credentials=credentials)

st.title("📸 Restaurant Receipt Splitter (OCR + Bill Sharing)")

uploaded_file = st.file_uploader("Upload a restaurant receipt", type=["png", "jpg", "jpeg"])
if uploaded_file:
    st.image(uploaded_file, caption="Uploaded Receipt", use_container_width=True)
    content = uploaded_file.read()

    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)
    text = response.full_text_annotation.text

    editable_text = st.text_area("🔍 OCR Text (editable)", value=text, height=300)

    if "parsed_items" not in st.session_state:
        st.session_state.parsed_items = []

    if st.button("Parse Items"):
        lines = [line.strip() for line in editable_text.split("\n") if line.strip()]
        items = []
        for line in lines:
            parts = line.rsplit(" ", 1)
            if len(parts) == 2:
                desc, price_str = parts
                try:
                    price = float(price_str.replace("$", "").replace(",", ""))
                    items.append({"id": str(uuid.uuid4()), "description": desc.strip(), "price": price})
                except ValueError:
                    continue
        st.session_state.parsed_items = items

    if st.session_state.get("parsed_items"):
        st.subheader("Parsed Items")
        for item in st.session_state.parsed_items:
            st.write(f"- {item['description']} - ${item['price']:.2f}")