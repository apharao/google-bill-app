
import streamlit as st
import json
import uuid
import io
from PIL import Image, ExifTags
from google.cloud import vision
from google.oauth2 import service_account
from fpdf import FPDF

# Load credentials
creds_info = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
credentials = service_account.Credentials.from_service_account_info(creds_info)
client = vision.ImageAnnotatorClient(credentials=credentials)

st.set_page_config(layout="wide")
st.title("📸 Smart Bill Splitter (Google OCR Edition)")

def fix_orientation(image):
    try:
        for orientation in ExifTags.TAGS:
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif:
            val = exif.get(orientation)
            if val == 3: image = image.rotate(180, expand=True)
            elif val == 6: image = image.rotate(270, expand=True)
            elif val == 8: image = image.rotate(90, expand=True)
    except:
        pass
    return image

def extract_text_google_vision(file):
    content = file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    return texts[0].description if texts else ""

def parse_items(text):
    lines = text.split('\n')
    items = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            price = float(line.split()[-1].replace('$', '').replace(',', ''))
            desc = " ".join(line.split()[:-1])
            items.append({"id": str(uuid.uuid4())[:8], "desc": desc.strip(), "price": price})
        except:
            items.append({"id": str(uuid.uuid4())[:8], "desc": line.strip(), "price": 0.00})
    return items

# State init
for key, val in {
    "raw_text": "",
    "items": [],
    "people": {},
    "edit_mode": False,
    "item_states": {}
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Upload
st.markdown("### Step 1: Upload Receipt Image")
file = st.file_uploader("Upload", type=["jpg", "jpeg", "png"])
if file and not st.session_state.raw_text:
    image = fix_orientation(Image.open(file))
    st.image(image, caption="Uploaded Image", use_container_width=True)
    st.session_state.raw_text = extract_text_google_vision(file)

# OCR and Edit
if st.session_state.raw_text:
    st.markdown("### Step 2: Edit OCR Text")
    st.session_state.raw_text = st.text_area("Scanned Text", st.session_state.raw_text, height=300)
    if st.button("Parse Items"):
        st.session_state.items = parse_items(st.session_state.raw_text)
        st.session_state.item_states = {item["id"]: {"selected": False} for item in st.session_state.items}

# Edit mode toggle
st.session_state.edit_mode = st.checkbox("Enable Manual Edit of Items")

# Item display and assignment
if not isinstance(st.session_state.items, list):
    st.session_state.items = []


if st.session_state.items:
    st.markdown("### Step 3: Assign Items")
    selected_ids = []
    with st.form("assign_form"):
        name = st.text_input("Person's Name")
        try:
            tax = st.number_input("Tax %", value=8.75, step=0.01)
        except:
            tax = 0.0
        try:
            tip = st.number_input("Tip %", value=15.0, step=0.5)
        except:
            tip = 0.0

        selected_ids = []
        for item in st.session_state.items:
            sid = item["id"]
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                new_desc = st.text_input(f"desc_{sid}", item["desc"], disabled=not st.session_state.edit_mode)
            with col2:
                new_price = st.number_input(f"price_{sid}", value=item["price"], step=0.01, format="%.2f",
                                            disabled=not st.session_state.edit_mode)
            with col3:
                checked = st.checkbox("Select", key=f"select_{sid}")
            item["desc"] = new_desc
            item["price"] = new_price
            if checked:
                selected_ids.append(sid)

        submit = st.form_submit_button("Assign Selected Items")
        if submit and name and selected_ids:
            if name not in st.session_state.people:
                st.session_state.people[name] = {"items": [], "tax": tax, "tip": tip}
            else:
                st.session_state.people[name]["tax"] = tax
                st.session_state.people[name]["tip"] = tip
            for sid in selected_ids:
                match = next(i for i in st.session_state.items if i["id"] == sid)
                st.session_state.people[name]["items"].append(match)
            st.session_state.items = [i for i in st.session_state.items if i["id"] not in selected_ids]
            st.experimental_rerun()

# Unassign support
if st.session_state.people:
    st.markdown("### Step 4: Review / Unassign")
    for name in list(st.session_state.people.keys()):
        person = st.session_state.people[name]
        st.subheader(f"{name}")
        unassign_ids = []
        for item in person["items"]:
            if st.checkbox(f"❌ {item['desc']} - ${item['price']:.2f}", key=f"un_{item['id']}"):
                unassign_ids.append(item["id"])
        if unassign_ids:
            person["items"] = [i for i in person["items"] if i["id"] not in unassign_ids]
            for uid in unassign_ids:
                st.session_state.items.append(next(i for i in st.session_state.people[name]["items"] if i["id"] == uid))
            if not person["items"]:
                del st.session_state.people[name]
            st.experimental_rerun()

# PDF export
if st.session_state.people:
    st.markdown("### Step 5: Export PDF Summary")
    if st.button("Generate PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for name, person in st.session_state.people.items():
            pdf.set_font("Arial", "B", 14)
            pdf.cell(200, 10, txt=name, ln=True)
            pdf.set_font("Arial", size=12)
            subtotal = sum(i["price"] for i in person["items"])
            tax_amt = subtotal * (person["tax"] / 100)
            tip_amt = (subtotal + tax_amt) * (person["tip"] / 100)
            total = subtotal + tax_amt + tip_amt
            for item in person["items"]:
                pdf.cell(200, 10, txt=f"{item['desc']} - ${item['price']:.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Subtotal: ${subtotal:.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Tax ({person['tax']}%): ${tax_amt:.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Tip ({person['tip']}%): ${tip_amt:.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Total: ${total:.2f}", ln=True)
            pdf.ln(10)
        path = "/mnt/data/final_bill_google_ocr_export.pdf"
        pdf.output(path)
        with open(path, "rb") as f:
            st.download_button("Download PDF", f, "bill_summary.pdf")

