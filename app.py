
import streamlit as st
import io
import uuid
from google.cloud import vision
from google.oauth2 import service_account
import json

# Set page config
st.set_page_config(page_title="Bill Splitter", layout="wide")

# Load credentials
credentials = service_account.Credentials.from_service_account_info(
    json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
)

client = vision.ImageAnnotatorClient(credentials=credentials)

def extract_text_from_image(image_bytes):
    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    return texts[0].description if texts else ""

def parse_items(raw_text, has_quantity):
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    items = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if has_quantity:
            try:
                desc = line
                qty = float(lines[i + 1])
                price = float(lines[i + 2])
                items.append({
                    "id": str(uuid.uuid4()),
                    "description": desc,
                    "price": price
                })
                i += 3
            except:
                i += 1
        else:
            try:
                desc = line
                price = float(lines[i + 1])
                items.append({
                    "id": str(uuid.uuid4()),
                    "description": desc,
                    "price": price
                })
                i += 2
            except:
                i += 1
    return items

st.title("📷 Receipt Splitter")

if "parsed_items" not in st.session_state:
    st.session_state.parsed_items = []

uploaded_file = st.file_uploader("Upload a receipt image", type=["png", "jpg", "jpeg"])
if uploaded_file:
    has_quantity = st.checkbox("Does the bill include quantities?", value=True)

    image_bytes = uploaded_file.read()
    st.image(image_bytes, caption="Uploaded Receipt", use_container_width=True)

    if st.button("Run OCR and Parse"):
        with st.spinner("Extracting and parsing text..."):
            text = extract_text_from_image(image_bytes)
            st.session_state.parsed_items = parse_items(text, has_quantity)

if st.session_state.parsed_items:
    st.subheader("🧾 Parsed Items")
    for item in st.session_state.parsed_items:
        col1, col2 = st.columns([4, 1])
        item["description"] = col1.text_input(
            f"Description for ${item['price']}", value=item["description"], key=f"desc_{item['id']}"
        )
        item["price"] = col2.text_input(
            f"Price for {item['description']}", value=str(item["price"]), key=f"price_{item['id']}"
        )
