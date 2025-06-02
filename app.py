
import streamlit as st
from google.cloud import vision
from google.oauth2 import service_account
import uuid
import re
import io
from PIL import Image

# Authenticate
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
)

# Vision client
client = vision.ImageAnnotatorClient(credentials=credentials)

st.set_page_config(page_title="Receipt Splitter", layout="centered")
st.title("📸 Restaurant Bill Splitter")
st.markdown("Upload a receipt and split it easily among people.")

uploaded_file = st.file_uploader("Upload Receipt Image", type=["png", "jpg", "jpeg"])
includes_quantity = st.checkbox("Does the receipt include quantities?")

if uploaded_file:
    image_bytes = uploaded_file.read()
    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)
    text = response.text_annotations[0].description if response.text_annotations else ""
    st.text_area("Extracted Text (editable)", value=text, key="ocr_text", height=300)

    if st.button("Parse Items"):
        lines = [line.strip() for line in st.session_state.ocr_text.split("\n") if line.strip()]
        items = []

        for line in lines:
            match = re.findall(r"([-\w\s\(\)]+?)\s+(\d+(?:\.\d{2})?)", line)
            if match:
                # if quantity is included, expect two numbers and use the second one
                if includes_quantity and len(match) > 1:
                    desc = match[0][0]
                    price = float(match[1][1])
                else:
                    desc = match[0][0]
                    price = float(match[0][1])

                items.append({
                    "id": str(uuid.uuid4()),
                    "description": desc.strip(),
                    "price": price
                })

        st.session_state.parsed_items = items

# Display parsed items
if "parsed_items" in st.session_state:
    st.subheader("Parsed Items")
    for item in st.session_state.parsed_items:
        st.write(f"{item['description']} - ${item['price']:.2f}")
