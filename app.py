import streamlit as st
import uuid
from google.cloud import vision
from google.oauth2 import service_account
import io
from PIL import Image
import json

# Load credentials
credentials = service_account.Credentials.from_service_account_info(
    json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
)

client = vision.ImageAnnotatorClient(credentials=credentials)

st.title("📸 Restaurant Bill Splitter")

uploaded_file = st.file_uploader("Upload your receipt image", type=["png", "jpg", "jpeg"])
include_quantity = st.checkbox("Does this receipt include a quantity column?", value=True)

def run_ocr(image_bytes):
    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)
    return response.text_annotations[0].description if response.text_annotations else ""

def parse_items(text, include_qty=True):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    items = []
    for i in range(len(lines) - 1):
        desc = lines[i]
        maybe_price = lines[i + 1]
        try:
            price = float(maybe_price.replace('$', '').strip())
            if include_qty:
                if i > 0 and lines[i - 1].replace('.', '', 1).isdigit():
                    continue
            item_id = str(uuid.uuid4())
            items.append({'id': item_id, 'description': desc, 'price': price})
        except ValueError:
            continue
    return items

if uploaded_file:
    image_bytes = uploaded_file.read()
    raw_text = run_ocr(image_bytes)
    st.text_area("OCR Output", value=raw_text, height=150)

    if "parsed_items" not in st.session_state:
        st.session_state.parsed_items = parse_items(raw_text, include_qty=include_quantity)
        st.session_state.assignments = {}

    st.subheader("Parsed Items")
    for item in st.session_state.parsed_items:
        item['description'] = st.text_input(f"Edit description for ${item['price']}", value=item['description'], key=item['id'])
        item['price'] = st.number_input(f"Edit price for {item['description']}", value=item['price'], key=f"{item['id']}_price")

    st.subheader("Assign Items")
    people = st.text_input("Enter names separated by commas (e.g., Alice,Bob)").split(",")
    for person in people:
        person = person.strip()
        if not person:
            continue
        st.markdown(f"**{person}**")
        with st.expander(f"Select items for {person}"):
            selected = st.multiselect(f"Items for {person}", [f"{item['description']} - ${item['price']}" for item in st.session_state.parsed_items], key=f"sel_{person}")
            tip = st.number_input(f"{person}'s Tip (%)", min_value=0.0, max_value=100.0, value=20.0, key=f"tip_{person}")
            tax = st.number_input(f"{person}'s Tax (%)", min_value=0.0, max_value=100.0, value=7.75, key=f"tax_{person}")
            total = 0
            for sel in selected:
                for item in st.session_state.parsed_items:
                    if sel.startswith(item['description']) and f"${item['price']}" in sel:
                        total += item['price']
            total += total * (tip + tax) / 100
            st.write(f"**Total for {person}: ${total:.2f}**")