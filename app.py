import streamlit as st
from google.cloud import vision
from google.oauth2 import service_account
import json
import uuid

st.set_page_config(page_title="Restaurant Bill Splitter", layout="wide")

# Load credentials properly using json.loads
credentials = service_account.Credentials.from_service_account_info(
    json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
)
client = vision.ImageAnnotatorClient(credentials=credentials)

def extract_text_from_image(uploaded_image):
    content = uploaded_image.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description
    return ""

def parse_receipt_text(text, includes_quantity=False):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    items = []
    for line in lines:
        parts = line.rsplit(" ", 2) if includes_quantity else line.rsplit(" ", 1)
        if len(parts) >= 2:
            try:
                price = float(parts[-1].replace("$", "").replace(",", ""))
                description = parts[0] if includes_quantity else parts[0]
                items.append({
                    "id": str(uuid.uuid4()),
                    "description": description.strip(),
                    "price": price
                })
            except ValueError:
                continue
    return items

st.title("📸 Restaurant Bill Splitter")

uploaded_file = st.file_uploader("Upload receipt image", type=["jpg", "jpeg", "png"])
if uploaded_file:
    st.image(uploaded_file, caption="Uploaded Receipt", use_container_width=True)
    receipt_text = extract_text_from_image(uploaded_file)
    editable_text = st.text_area("Edit OCR Text", receipt_text, height=300)
    includes_quantity = st.checkbox("Does the bill include quantities?", value=True)
    if st.button("Parse Items"):
        parsed_items = parse_receipt_text(editable_text, includes_quantity)
        st.session_state.parsed_items = parsed_items
        st.success("Parsed items updated.")

if "parsed_items" in st.session_state:
    st.subheader("Parsed Items")
    for item in st.session_state.parsed_items:
        st.write(f"{item['description']} - ${item['price']:.2f}")
# Minor change to force deployment
