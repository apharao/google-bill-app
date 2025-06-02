
import streamlit as st
from google.cloud import vision
import io
import uuid
from fpdf import FPDF

# Session state init
if "items" not in st.session_state:
    st.session_state.items = []
if "people" not in st.session_state:
    st.session_state.people = []
if "assigned_items" not in st.session_state:
    st.session_state.assigned_items = {}
if "person_data" not in st.session_state:
    st.session_state.person_data = {}
if "current_person_index" not in st.session_state:
    st.session_state.current_person_index = 0
if "receipt_parsed" not in st.session_state:
    st.session_state.receipt_parsed = False

st.title("Receipt Splitter")

# Step 1: Upload and OCR
image_file = st.file_uploader("Upload a receipt image", type=["jpg", "jpeg", "png"])
quantity_toggle = st.checkbox("Receipt includes quantities")

def ocr_image(file):
    client = vision.ImageAnnotatorClient()
    content = file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    return texts[0].description if texts else ""

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
    st.session_state.receipt_parsed = True
    st.success("Receipt parsed successfully!")

# Step 2: Edit items
if st.session_state.receipt_parsed:
    st.subheader("Edit Parsed Items")
    for item in st.session_state.items:
        item["description"] = st.text_input("Description", value=item["description"], key=f"desc_{item['id']}")
        item["price"] = st.number_input("Price", value=item["price"], key=f"price_{item['id']}", step=0.01)

    # Step 3: Add people
    st.subheader("Add People")
    with st.form("add_person_form"):
        name = st.text_input("Person's Name")
        submit = st.form_submit_button("Add Person")
        if submit and name:
            if name not in st.session_state.people:
                st.session_state.people.append(name)
                st.session_state.person_data[name] = {"items": [], "tip": 0.0, "tax": 0.0}

# Step 4: Per-person assignment
if st.session_state.people and st.session_state.receipt_parsed:
    person = st.session_state.people[st.session_state.current_person_index]
    st.subheader(f"{person}'s Turn")

    unassigned_items = [item for item in st.session_state.items if item["id"] not in st.session_state.assigned_items or st.session_state.assigned_items[item["id"]] == person]
    options = [f"{item['description']} - ${item['price']}" for item in unassigned_items]

    selected = st.multiselect("Select items for this person", options, key=f"select_{person}")
    tip = st.number_input("Tip amount", min_value=0.0, step=0.01, key=f"tip_{person}")
    tax = st.number_input("Tax amount", min_value=0.0, step=0.01, key=f"tax_{person}")

    if st.button("Confirm Selection"):
        for s in selected:
            for item in unassigned_items:
                label = f"{item['description']} - ${item['price']}"
                if label == s:
                    st.session_state.assigned_items[item["id"]] = person
                    st.session_state.person_data[person]["items"].append(item)
        st.session_state.person_data[person]["tip"] = tip
        st.session_state.person_data[person]["tax"] = tax

        if st.session_state.current_person_index < len(st.session_state.people) - 1:
            st.session_state.current_person_index += 1
        else:
            st.success("All people have selected items.")

# Step 5: PDF export
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for person, pdata in st.session_state.person_data.items():
        pdf.set_font(style="B")
        pdf.cell(200, 10, f"{person}:", ln=True)
        pdf.set_font(style="")
        total = sum(item["price"] for item in pdata["items"])
        for item in pdata["items"]:
            pdf.cell(200, 10, f" - {item['description']}: ${item['price']:.2f}", ln=True)
        pdf.cell(200, 10, f"Tax: ${pdata['tax']:.2f}", ln=True)
        pdf.cell(200, 10, f"Tip: ${pdata['tip']:.2f}", ln=True)
        pdf.cell(200, 10, f"Total: ${total + pdata['tax'] + pdata['tip']:.2f}", ln=True)
        pdf.ln()
    pdf.output("/mnt/data/bill_summary.pdf")

if st.session_state.people and st.session_state.current_person_index == len(st.session_state.people) - 1:
    if st.button("Generate Final PDF"):
        generate_pdf()
        st.download_button("Download PDF", data=open("/mnt/data/bill_summary.pdf", "rb"), file_name="bill_summary.pdf")
