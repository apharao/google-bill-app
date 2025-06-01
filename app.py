
import streamlit as st
import json
import uuid
from PIL import Image, ExifTags
from google.cloud import vision
from google.oauth2 import service_account
from fpdf import FPDF

# --- Init Google Cloud Vision client ---
creds_info = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
credentials = service_account.Credentials.from_service_account_info(creds_info)
client = vision.ImageAnnotatorClient(credentials=credentials)

# --- Page Setup ---
st.set_page_config(layout="wide")
st.title("📸 Smart Bill Splitter (Google OCR Edition)")

# --- Orientation Fix ---
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

# --- Google OCR ---
def extract_text_google_vision(file):
    content = file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    return texts[0].description if texts else ""

# --- Parse Items ---
def parse_items(text):
    lines = text.split('\n')
    parsed = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if "discount" in line.lower():
            i += 1
            continue
        try:
            price = float(line.split()[-1].replace('$', '').replace(',', ''))
            desc = " ".join(line.split()[:-1])
            parsed.append({"id": str(uuid.uuid4())[:8], "desc": desc.strip(), "price": price})
        except:
            pass
        i += 1
    return parsed

# --- Initialize State ---
if "raw_text" not in st.session_state:
    st.session_state.raw_text = ""
if "items" not in st.session_state:
    st.session_state.items = []
if "people" not in st.session_state:
    st.session_state.people = {}
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
if "selected_ids" not in st.session_state:
    st.session_state.selected_ids = []

# --- Upload and OCR ---
st.markdown("### Step 1: Upload Receipt")
file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
if file and not st.session_state.raw_text:
    image = fix_orientation(Image.open(file))
    st.image(image, caption="Uploaded Receipt", use_container_width=True)
    st.session_state.raw_text = extract_text_google_vision(file)

# --- Raw OCR Edit ---
if st.session_state.raw_text:
    st.markdown("### Step 2: Edit Text from Receipt")
    st.session_state.raw_text = st.text_area("OCR Output", st.session_state.raw_text, height=250)
    if st.button("Parse Items"):
        st.session_state.items = parse_items(st.session_state.raw_text)
        st.session_state.selected_ids = []

# --- Assignment Form ---
if st.session_state.items:
    st.markdown("### Step 3: Assign Items to a Person")
    with st.form("assign_form"):
        name = st.text_input("Name")
        tax = st.number_input("Tax %", value=8.75, step=0.01)
        tip = st.number_input("Tip %", value=15.0, step=0.5)
        selected_ids = []
        for item in st.session_state.items:
            cols = st.columns([6, 2, 1])
            with cols[0]:
                desc = st.text_input(f"desc_{item['id']}", item["desc"], key=f"desc_{item['id']}")
            with cols[1]:
                price = st.number_input(f"price_{item['id']}", value=item["price"], step=0.01, key=f"price_{item['id']}")
            with cols[2]:
                checked = st.checkbox("✔", key=f"check_{item['id']}")
            item["desc"] = desc
            item["price"] = price
            if checked:
                selected_ids.append(item["id"])
        submitted = st.form_submit_button("✅ Assign Selected Items")
        if submitted and name and selected_ids:
            if name not in st.session_state.people:
                st.session_state.people[name] = {"items": [], "tax": tax, "tip": tip}
            else:
                st.session_state.people[name]["tax"] = tax
                st.session_state.people[name]["tip"] = tip
            selected_items = [item for item in st.session_state.items if item["id"] in selected_ids]
            st.session_state.people[name]["items"].extend(selected_items)
            st.session_state.items = [item for item in st.session_state.items if item["id"] not in selected_ids]
            st.experimental_rerun()

# --- Unassign ---
if st.session_state.people:
    st.markdown("### Step 4: Review and Unassign")
    for person, data in list(st.session_state.people.items()):
        st.subheader(person)
        to_remove = []
        for item in data["items"]:
            if st.checkbox(f"❌ {item['desc']} - ${item['price']:.2f}", key=f"un_{item['id']}"):
                to_remove.append(item["id"])
        if to_remove:
            data["items"] = [i for i in data["items"] if i["id"] not in to_remove]
            st.session_state.items.extend([i for i in st.session_state.people[person]["items"] if i["id"] in to_remove])
            if not data["items"]:
                del st.session_state.people[person]
            st.experimental_rerun()

# --- Export PDF ---
if st.session_state.people:
    st.markdown("### Step 5: Export Bill as PDF")
    if st.button("Generate PDF Summary"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for name, data in st.session_state.people.items():
            pdf.set_font("Arial", "B", 14)
            pdf.cell(200, 10, txt=name, ln=True)
            pdf.set_font("Arial", size=12)
            subtotal = sum(i["price"] for i in data["items"])
            tax_amt = subtotal * (data["tax"] / 100)
            tip_amt = (subtotal + tax_amt) * (data["tip"] / 100)
            total = subtotal + tax_amt + tip_amt
            for item in data["items"]:
                pdf.cell(200, 10, txt=f"{item['desc']} - ${item['price']:.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Subtotal: ${subtotal:.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Tax ({data['tax']}%): ${tax_amt:.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Tip ({data['tip']}%): ${tip_amt:.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Total: ${total:.2f}", ln=True)
            pdf.ln(8)
        path = "/mnt/data/final_bill_summary.pdf"
        pdf.output(path)
        with open(path, "rb") as f:
            st.download_button("📄 Download Final PDF", f, "bill_summary.pdf")
