# main.py
import streamlit as st
from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image, ExifTags
import io
import re
from fpdf import FPDF

# --- GOOGLE CLOUD VISION SETUP ---
if "GOOGLE_APPLICATION_CREDENTIALS_JSON" not in st.secrets:
    st.error("Google credentials not found in Streamlit secrets.")
    st.stop()

import json
credentials = service_account.Credentials.from_service_account_info(
    json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
)
vision_client = vision.ImageAnnotatorClient(credentials=credentials)

# --- SESSION STATE ---
if "parsed_items" not in st.session_state:
    st.session_state.parsed_items = []
if "assignments" not in st.session_state:
    st.session_state.assignments = {}

# --- STEP 1: Upload and OCR ---
st.title("📸 Restaurant Bill Splitter")

uploaded_file = st.file_uploader("Upload a photo of your receipt", type=["png", "jpg", "jpeg"])
if uploaded_file:
    image = Image.open(uploaded_file)

    # Fix EXIF orientation
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(image._getexif().items())
        if exif[orientation] == 3:
            image = image.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image = image.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image = image.rotate(90, expand=True)
    except:
        pass

    st.image(image, caption="Uploaded Receipt", use_container_width=True)

    # OCR
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    content = img_byte_arr.getvalue()

    image_google = vision.Image(content=content)
    response = vision_client.text_detection(image=image_google)
    texts = response.text_annotations
    if not texts:
        st.error("No text detected.")
        st.stop()

    raw_text = texts[0].description
    editable_text = st.text_area("OCR Output - Edit if needed", raw_text, height=300)

    # --- STEP 2: Parse and Display Items ---
    
    def parse_items(text):
        lines = text.split("\n")
        items = []
        pattern = re.compile(r"(.+?)\s+\$?(-?\d+\.\d{2})$")
        discount_pattern = re.compile(r"(discount.*?-?\$\d+\.\d{2})", re.IGNORECASE)
        skip_keywords = ["subtotal", "total", "tax", "tip", "change", "cash", "payment", "visa", "mastercard"]

        st.markdown("### Debug: Parsed Lines")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if any(word in stripped.lower() for word in skip_keywords):
                st.text(f"Skipping: {stripped}")
                continue
            match = pattern.search(stripped)
            if match:
                desc, price = match.groups()
                item = {"id": str(uuid.uuid4()), "description": desc.strip(), "price": float(price)}
                st.text(f"Matched: {item}")
                items.append(item)
            elif discount_pattern.search(stripped) and items:
                discount = float(re.findall(r"-?\$([\d\.]+)", stripped)[-1])
                items[-1]["price"] -= discount
                items[-1]["description"] += " (discount applied)"
                st.text(f"Applied discount to: {items[-1]}")
            else:
                st.text(f"No match: {stripped}")
        return items

st.session_state.parsed_items = parse_items(editable_text)

    st.subheader("Parsed Items")
    for item in st.session_state.parsed_items:
        st.write(f"{item['description']} - ${item['price']:.2f}")

# --- STEP 3: Assign Items ---



st.subheader("Assign Items")

assigned_ids = {item["id"] for v in st.session_state.assignments.values() for item in v["items"]}
unassigned_items = [i for i in st.session_state.parsed_items if i["id"] not in assigned_ids] if "parsed_items" in st.session_state else []

name = st.text_input("Name", key="name_input")
tax_rate = st.number_input("Tax %", min_value=0.0, max_value=100.0, step=0.1, key="tax_input")
tip_rate = st.number_input("Tip %", min_value=0.0, max_value=100.0, step=0.1, key="tip_input")

selected = []
if unassigned_items:
    for item in unassigned_items:
        label = f"{item['description']} - ${item['price']:.2f}"
        if st.checkbox(label, key=f"item_{item['id']}"):
            selected.append(item)
else:
    st.info("No items available to assign yet.")

if st.button("Assign to Person") and name and selected:
    if name not in st.session_state.assignments:
        st.session_state.assignments[name] = {"tax": tax_rate, "tip": tip_rate, "items": []}
    st.session_state.assignments[name]["items"].extend(selected)
# Unassign option
    st.subheader("Current Assignments")
    for person, data in st.session_state.assignments.items():
        st.markdown(f"**{person}**")
        for item in data["items"]:
            if st.button(f"Unassign {item['description']} from {person}", key=f"unassign_{person}_{item['description']}"):
                data["items"].remove(item)


# --- STEP 3B: Current Assignments and Unassign ---
st.subheader("Current Assignments")

for person, data in st.session_state.assignments.items():
    st.markdown(f"**{person}**")
    for item in data["items"]:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"- ~~{item['description']} - ${item['price']:.2f}~~")
        with col2:
            if st.button("❌", key=f"unassign_{person}_{item['id']}"):
                data["items"].remove(item)

# --- STEP 4: Manual Editing ---
if st.session_state.parsed_items:
    st.subheader("Edit Items")
    for item in st.session_state.parsed_items:
        item['description'] = st.text_input(f"Edit description:", value=item['description'], key=f"desc_{item['description']}")
        item['price'] = st.number_input(f"Edit price:", value=item['price'], key=f"price_{item['description']}")

# --- STEP 5 & 6: Calculations and Export ---
if st.button("Finish and Export PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for person, data in st.session_state.assignments.items():
        pdf.set_font(style="B")
        pdf.cell(200, 10, txt=person, ln=True)
        pdf.set_font(style="")

        subtotal = sum(item['price'] for item in data['items'])
        tax = subtotal * (data['tax'] / 100)
        tip = (subtotal + tax) * (data['tip'] / 100)
        total = subtotal + tax + tip

        for item in data['items']:
            pdf.cell(200, 10, txt=f"{item['description']} - ${item['price']:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Subtotal: ${subtotal:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Tax ({data['tax']}%): ${tax:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Tip ({data['tip']}%): ${tip:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Total: ${total:.2f}", ln=True)
        pdf.ln(10)
