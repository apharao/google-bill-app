
import streamlit as st
from PIL import Image
import pytesseract
from fpdf import FPDF
import uuid

st.set_page_config(layout="wide")
st.title("📸 Smart Multi-Person Bill Splitter")

# Proper session state initialization
if "receipt_items" not in st.session_state:
    st.session_state.receipt_items = []
if "claimed" not in st.session_state:
    st.session_state.claimed = []
if "people" not in st.session_state:
    st.session_state.people = []
if "raw_text" not in st.session_state:
    st.session_state.raw_text = ""
if "item_id_map" not in st.session_state:
    st.session_state.item_id_map = {}
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

def extract_items(raw_text):
    lines = raw_text.splitlines()
    parsed_items = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or "quantity" in line.lower():
            i += 1
            continue
        parts = line.rsplit(" ", 1)
        if len(parts) == 2 and parts[1].replace('.', '', 1).lstrip('-').isdigit():
            name, price_str = parts[0], parts[1]
            price = float(price_str)
            key = f"{name.strip()}_{price:.2f}_{i}"
            uid = st.session_state.item_id_map.get(key, str(uuid.uuid4())[:8])
            st.session_state.item_id_map[key] = uid
            discount = 0.0
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if "discount" in next_line.lower() and "-" in next_line:
                    next_parts = next_line.rsplit(" ", 1)
                    if len(next_parts) == 2:
                        try:
                            discount = float(next_parts[1].replace('$', '').replace('-', ''))
                            i += 1
                        except:
                            pass
            final_price = round(price - discount, 2)
            parsed_items.append({
                "id": uid,
                "item": name,
                "original": price,
                "discount": discount,
                "price": final_price
            })
        i += 1
    return parsed_items

def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for person in data:
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, f"{person['name']}", ln=True)
        pdf.set_font("Arial", size=12)
        # ✅ Show 2 decimal places
        pdf.cell(200, 10, f"Tax: {person['tax']*100:.2f}%, Tip: {person['tip']*100:.2f}%", ln=True)
        pdf.ln(3)
        for item in person["items"]:
            pdf.cell(200, 10, f"{item['item']} - ${item['price']:.2f}", ln=True)
        pdf.ln(2)
        pdf.cell(200, 10, f"Subtotal: ${person['subtotal']:.2f}", ln=True)
        pdf.cell(200, 10, f"Tax: ${person['tax_amt']:.2f}", ln=True)
        pdf.cell(200, 10, f"Tip: ${person['tip_amt']:.2f}", ln=True)
        pdf.cell(200, 10, f"Total: ${person['total']:.2f}", ln=True)
        pdf.ln(10)
    out_path = "final_bill_summary_precise.pdf"
    pdf.output(out_path)
    return out_path

# Upload & OCR
st.markdown("### Step 1: Upload Receipt")
file = st.file_uploader("Upload a receipt image", type=["jpg", "jpeg", "png"])
if file and not st.session_state.raw_text:
    image = Image.open(file)
    st.image(image, caption="Uploaded Receipt", use_container_width=True)
    raw = pytesseract.image_to_string(image)
    st.session_state.raw_text = raw
    st.session_state.receipt_items = extract_items(raw)

# Manual edit mode
st.markdown("### Edit Items (optional)")
if st.checkbox("✏️ Enable Edit Mode", value=st.session_state.edit_mode):
    st.session_state.edit_mode = True
    for item in st.session_state.receipt_items:
        item["item"] = st.text_input(f"Edit name for item {item['id']}", value=item["item"], key=f"edit_name_{item['id']}")
        item["price"] = float(st.text_input(f"Edit price for {item['item']}", value=f"{item['price']:.2f}", key=f"edit_price_{item['id']}"))
else:
    st.session_state.edit_mode = False

# Assigning
st.markdown("### Step 2: Assign Items to a Person")
name = st.text_input("Name")
tax = st.text_input("Tax %", "8")
tip = st.text_input("Tip %", "18")
try: tax = float(tax) / 100
except: tax = 0.08
try: tip = float(tip) / 100
except: tip = 0.18

for item in st.session_state.receipt_items:
    if item["id"] not in st.session_state.claimed:
        if f"item_{item['id']}" not in st.session_state:
            st.session_state[f"item_{item['id']}"] = False
        st.checkbox(f"{item['item']} - ${item['price']:.2f}", key=f"item_{item['id']}")

if st.button("Assign Selected Items"):
    selected_ids = [item["id"] for item in st.session_state.receipt_items
                    if not item["id"] in st.session_state.claimed and st.session_state.get(f"item_{item['id']}", False)]
    if not name or not selected_ids:
        st.warning("Enter a name and select at least one item.")
    else:
        selected = [i for i in st.session_state.receipt_items if i["id"] in selected_ids]
        for sid in selected_ids:
            st.session_state.claimed.append(sid)
        subtotal = sum(i["price"] for i in selected)
        tax_amt = round(subtotal * tax, 2)
        tip_amt = round((subtotal + tax_amt) * tip, 2)
        total = round(subtotal + tax_amt + tip_amt, 2)
        st.session_state.people.append({
            "name": name,
            "tax": tax,
            "tip": tip,
            "items": selected,
            "subtotal": subtotal,
            "tax_amt": tax_amt,
            "tip_amt": tip_amt,
            "total": total
        })

# Unassign
if st.session_state.people:
    st.markdown("### ✅ Assigned Summary (Click to Unassign)")
    for p in st.session_state.people:
        st.markdown(f"**{p['name']}**")
        to_remove = []
        for i in p["items"]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"- ~~{i['item']} - ${i['price']:.2f}~~")
            with col2:
                if st.button(f"❌ Unassign", key=f"unassign_{p['name']}_{i['id']}"):
                    st.session_state.claimed.remove(i["id"])
                    to_remove.append(i["id"])
        if to_remove:
            p["items"] = [it for it in p["items"] if it["id"] not in to_remove]
            p["subtotal"] = sum(i["price"] for i in p["items"])
            p["tax_amt"] = round(p["subtotal"] * p["tax"], 2)
            p["tip_amt"] = round((p["subtotal"] + p["tax_amt"]) * p["tip"], 2)
            p["total"] = round(p["subtotal"] + p["tax_amt"] + p["tip_amt"], 2)
    st.session_state.people = [p for p in st.session_state.people if p["items"]]

# Remaining
remaining = [i for i in st.session_state.receipt_items if i["id"] not in st.session_state.claimed]
if remaining:
    st.markdown("### 🧾 Remaining:")
    for i in remaining:
        st.markdown(f"- {i['item']} - ${i['price']:.2f}")

# Export
if not remaining and st.session_state.people:
    if st.button("📄 Export PDF Summary"):
        path = generate_pdf(st.session_state.people)
        with open(path, "rb") as f:
            st.download_button("Download PDF", f, file_name="bill_summary_precise.pdf", mime="application/pdf")


# Footer
st.markdown("""
---
App created by **Alexis Gonzalez**  
Protected under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)  
[GitHub Repo](https://github.com/YOUR_USERNAME/YOUR_REPO)
""")
