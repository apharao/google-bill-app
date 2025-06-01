
import streamlit as st
import json
import uuid
import io
from PIL import Image, ExifTags
from google.cloud import vision
from google.oauth2 import service_account
from fpdf import FPDF

# Load Google credentials from Streamlit secrets
creds_info = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
credentials = service_account.Credentials.from_service_account_info(creds_info)
client = vision.ImageAnnotatorClient(credentials=credentials)

st.set_page_config(layout="wide")
st.title("📸 Smart Bill Splitter with Google Vision OCR")

def fix_orientation(image):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif:
            orientation_value = exif.get(orientation)
            if orientation_value == 3:
                image = image.rotate(180, expand=True)
            elif orientation_value == 6:
                image = image.rotate(270, expand=True)
            elif orientation_value == 8:
                image = image.rotate(90, expand=True)
    except:
        pass
    return image

def extract_text_google_vision(file):
    content = file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description
    return ""

def parse_items(text):
    items = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if i + 1 < len(lines) and "discount" in lines[i + 1].lower():
            price_line = lines[i + 1].strip()
            try:
                price = float(price_line.replace("$", "").replace("−", "-").replace(",", "").split()[-1])
                items.append({"desc": line, "price": price})
                i += 2
                continue
            except:
                pass
        try:
            price = float(line.replace("$", "").replace(",", "").split()[-1])
            desc = " ".join(line.split()[:-1])
            items.append({"desc": desc if desc else f"Item {i}", "price": price})
        except:
            items.append({"desc": line, "price": 0.00})
        i += 1
    return items

if "raw_text" not in st.session_state:
    st.session_state.raw_text = ""
if "items" not in st.session_state:
    st.session_state.items = []
if "people" not in st.session_state:
    st.session_state.people = {}
if "item_map" not in st.session_state:
    st.session_state.item_map = {}

st.markdown("### Step 1: Upload Receipt Image")
uploaded_file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])

if uploaded_file and not st.session_state.raw_text:
    image = Image.open(uploaded_file)
    image = fix_orientation(image)
    st.image(image, caption="Uploaded Receipt", use_container_width=True)
    st.session_state.raw_text = extract_text_google_vision(uploaded_file)

if st.session_state.raw_text:
    st.markdown("### Step 2: Review & Edit Extracted Text")
    st.session_state.raw_text = st.text_area("Edit receipt text", st.session_state.raw_text, height=250)
    if st.button("Parse Items"):
        st.session_state.items = parse_items(st.session_state.raw_text)
        st.session_state.item_map = {str(uuid.uuid4())[:8]: item for item in st.session_state.items}

if st.session_state.item_map:
    st.markdown("### Step 3: Assign Items to People")
    with st.form("assign_form"):
        name = st.text_input("Name")
        tax = st.number_input("Tax %", value=8.75, step=0.01)
        tip = st.number_input("Tip %", value=15.0, step=0.5)
        selected_ids = []
        for uid, item in st.session_state.item_map.items():
            label = f"{item['desc']} - ${item['price']:.2f}"
            if st.checkbox(label, key=f"check_{uid}"):
                selected_ids.append(uid)
        submitted = st.form_submit_button("Assign Selected Items")
        if submitted and name and selected_ids:
            if name not in st.session_state.people:
                st.session_state.people[name] = {"items": [], "tax": tax, "tip": tip}
            st.session_state.people[name]["tax"] = tax
            st.session_state.people[name]["tip"] = tip
            for uid in selected_ids:
                st.session_state.people[name]["items"].append(st.session_state.item_map[uid])
                del st.session_state.item_map[uid]
            st.experimental_rerun()

    st.markdown("### Remaining Items")
    for item in st.session_state.item_map.values():
        st.write(f"{item['desc']} - ${item['price']:.2f}")

if st.session_state.people:
    st.markdown("### Assigned Summary")
    for name, pdata in st.session_state.people.items():
        st.subheader(f"{name}")
        subtotal = sum(i['price'] for i in pdata["items"])
        tax_amt = subtotal * (pdata["tax"] / 100)
        tip_amt = (subtotal + tax_amt) * (pdata["tip"] / 100)
        total = subtotal + tax_amt + tip_amt
        for item in pdata["items"]:
            st.write(f"✅ {item['desc']} - ${item['price']:.2f}")
        st.write(f"Subtotal: ${subtotal:.2f}")
        st.write(f"Tax ({pdata['tax']}%): ${tax_amt:.2f}")
        st.write(f"Tip ({pdata['tip']}%): ${tip_amt:.2f}")
        st.write(f"**Total: ${total:.2f}**")

    if st.button("Export PDF Summary"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for name, pdata in st.session_state.people.items():
            pdf.set_font("Arial", "B", 14)
            pdf.cell(200, 10, txt=f"{name}", ln=True)
            pdf.set_font("Arial", size=12)
            for item in pdata["items"]:
                pdf.cell(200, 10, txt=f"{item['desc']} - ${item['price']:.2f}", ln=True)
            subtotal = sum(i['price'] for i in pdata["items"])
            tax_amt = subtotal * (pdata["tax"] / 100)
            tip_amt = (subtotal + tax_amt) * (pdata["tip"] / 100)
            total = subtotal + tax_amt + tip_amt
            pdf.cell(200, 10, txt=f"Subtotal: ${subtotal:.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Tax ({pdata['tax']}%): ${tax_amt:.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Tip ({pdata['tip']}%): ${tip_amt:.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Total: ${total:.2f}", ln=True)
            pdf.ln(10)
        out_path = "/mnt/data/final_bill_summary_google_ocr.pdf"
        pdf.output(out_path)
        st.success("PDF exported!")
        st.download_button("Download PDF", data=open(out_path, "rb").read(), file_name="bill_summary.pdf")

