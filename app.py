
import streamlit as st
from google.cloud import vision
import io
import uuid
from fpdf import FPDF

# Initialize session state
if "items" not in st.session_state:
    st.session_state.items = []
if "people" not in st.session_state:
    st.session_state.people = []
if "assigned_items" not in st.session_state:
    st.session_state.assigned_items = {}
if "current_person_index" not in st.session_state:
    st.session_state.current_person_index = 0

st.title("Receipt Splitter App")

# Upload receipt image
image_file = st.file_uploader("Upload a receipt image", type=["jpg", "jpeg", "png"])

# Quantity toggle
quantity_toggle = st.checkbox("Receipt includes quantities")

# Google OCR function
def ocr_image(file):
    client = vision.ImageAnnotatorClient()
    content = file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    return texts[0].description if texts else ""

# Parse OCR text
def parse_receipt(text, quantity=False):
    lines = text.split("\n")
    parsed = []
    for line in lines:
        parts = line.strip().rsplit(" ", 2 if quantity else 1)
        if len(parts) >= 2:
            try:
                price = float(parts[-1].replace("$", "").replace(",", ""))
                description = " ".join(parts[:-1]) if not quantity else " ".join(parts[:-2])
                parsed.append({"id": str(uuid.uuid4()), "description": description, "price": price})
            except:
                continue
    return parsed

if image_file and st.button("Parse Receipt"):
    text = ocr_image(image_file)
    st.session_state.items = parse_receipt(text, quantity_toggle)
    st.success("Receipt parsed successfully!")

# Item editor
st.subheader("Edit Items")
for item in st.session_state.items:
    item["description"] = st.text_input(f"Item Description", value=item["description"], key=f"desc_{item['id']}")
    item["price"] = st.number_input("Price", value=item["price"], key=f"price_{item['id']}", step=0.01)

# Add person
with st.form("add_person"):
    new_name = st.text_input("Person's Name")
    submit = st.form_submit_button("Add")
    if submit and new_name:
        if new_name not in st.session_state.people:
            st.session_state.people.append(new_name)

# Assignment logic
if st.session_state.people:
    person = st.session_state.people[st.session_state.current_person_index]
    st.subheader(f"{person}'s turn to select items")

    unassigned_items = [
        item for item in st.session_state.items 
        if item["id"] not in st.session_state.assigned_items or st.session_state.assigned_items[item["id"]] == person
    ]

    selected = st.multiselect("Select your items", [f"{item['description']} - ${item['price']}" for item in unassigned_items], key=f"select_{person}")

    if st.button("Confirm selection"):
        for s in selected:
            for item in unassigned_items:
                label = f"{item['description']} - ${item['price']}"
                if label == s:
                    st.session_state.assigned_items[item["id"]] = person
        if st.session_state.current_person_index < len(st.session_state.people) - 1:
            st.session_state.current_person_index += 1
        else:
            st.success("All items assigned!")

# PDF export
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for person in st.session_state.people:
        pdf.set_font(style="B")
        pdf.cell(200, 10, f"{person}:", ln=True)
        pdf.set_font(style="")
        total = 0
        for item_id, assigned_to in st.session_state.assigned_items.items():
            if assigned_to == person:
                item = next(i for i in st.session_state.items if i["id"] == item_id)
                pdf.cell(200, 10, f" - {item['description']}: ${item['price']}", ln=True)
                total += item["price"]
        pdf.cell(200, 10, f"Total: ${total:.2f}", ln=True)
        pdf.ln()
    pdf.output("/mnt/data/bill_summary.pdf")

if st.button("Generate PDF"):
    generate_pdf()
    st.success("PDF generated!")
    st.download_button("Download PDF", data=open("/mnt/data/bill_summary.pdf", "rb"), file_name="bill_summary.pdf")
