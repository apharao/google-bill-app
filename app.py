
import streamlit as st
from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image, ExifTags
import io
import re
import json
import uuid
from fpdf import FPDF

# --- GOOGLE CLOUD VISION SETUP ---
if "GOOGLE_APPLICATION_CREDENTIALS_JSON" not in st.secrets:
    st.error("Google credentials not found in Streamlit secrets.")
    st.stop()

credentials = service_account.Credentials.from_service_account_info(
    json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
)
vision_client = vision.ImageAnnotatorClient(credentials=credentials)

# --- FUNCTION: PARSE ITEMS ---


def parse_items(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    items = []
    skip_keywords = ["subtotal", "total", "tax", "tip", "change", "cash", "payment", "visa", "mastercard"]
    discount_keywords = ["discount", "happy hour"]

    st.markdown("### Debug: Parsed Lines")
    i = 0
    while i < len(lines) - 2:
        desc = lines[i]
        qty = lines[i + 1]  # ignored
        price = lines[i + 2]

        # Check if discount
        if any(k in desc.lower() for k in discount_keywords):
            st.text(f"Discount line detected: {desc}")
            if items:
                try:
                    discount = float(price.replace("$", "").replace(",", ""))
                    items[-1]["price"] += discount  # discount is negative
                    items[-1]["description"] += " (discount applied)"
                    st.text(f"Applied discount {discount} to previous item: {items[-1]}")
                    i += 3
                    continue
                except ValueError:
                    st.text(f"Invalid discount price: {price}")
                    i += 1
                    continue
            else:
                st.text("Warning: discount appeared before any item")
                i += 1
                continue

        try:
            float_price = float(price.replace("$", "").replace(",", ""))
            item = {
                "id": str(uuid.uuid4()),
                "description": desc,
                "price": float_price
            }
            st.text(f"Matched: {item}")
            items.append(item)
            i += 3
        except ValueError:
            st.text(f"No match: {desc}, {qty}, {price}")
            i += 1

    return items


st.session_state.parsed_items = parse_items(editable_text)

    st.subheader("Parsed Items")
    if st.session_state.parsed_items:
        for item in st.session_state.parsed_items:
            st.write(f"{item['description']} - ${item['price']:.2f}")
    else:
        st.warning("No items were parsed. Check the debug output above.")

# --- STEP 3: Assign Items ---
st.subheader("Assign Items")
assigned_ids = {item["id"] for v in st.session_state.assignments.values() for item in v["items"]}
unassigned_items = [i for i in st.session_state.parsed_items if i["id"] not in assigned_ids] if st.session_state.parsed_items else []

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
st.subheader("Edit Items")
for item in st.session_state.parsed_items:
    item['description'] = st.text_input(f"Edit description:", value=item['description'], key=f"desc_{item['id']}")
    item['price'] = st.number_input(f"Edit price:", value=item['price'], key=f"price_{item['id']}")

# --- STEP 5 & 6: Export ---
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

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    st.download_button(label="Download PDF Summary", data=pdf_output.getvalue(), file_name="bill_summary.pdf", mime="application/pdf")
