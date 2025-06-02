
import streamlit as st
import uuid
from fpdf import FPDF

# Initialize session state
if "people_data" not in st.session_state:
    st.session_state.people_data = []
if "current_person_index" not in st.session_state:
    st.session_state.current_person_index = 0
if "tax_rate" not in st.session_state:
    st.session_state.tax_rate = 0.0

st.title("Bill Splitter with Tax & Tip")

# Step 1: Set tax rate once
if st.session_state.current_person_index == 0:
    st.session_state.tax_rate = st.number_input("Enter tax rate (%) for everyone", min_value=0.0, step=0.01)

# Step 2: Per person input
st.header(f"Person #{st.session_state.current_person_index + 1}")

with st.form("person_form"):
    name = st.text_input("Enter person's name")
    tip_percent = st.number_input("Enter tip percentage for this person", min_value=0.0, step=0.01)

    item_data = []
    num_items = st.number_input("How many items for this person?", min_value=1, step=1, value=1)

    for i in range(int(num_items)):
        desc = st.text_input(f"Item {i+1} Description", key=f"desc_{i}")
        price = st.number_input(f"Item {i+1} Price", min_value=0.0, step=0.01, key=f"price_{i}")
        item_data.append({"description": desc, "price": price})

    submitted = st.form_submit_button("Add Person and Continue")

    if submitted and name and all(item["description"] and item["price"] >= 0 for item in item_data):
        st.session_state.people_data.append({
            "name": name,
            "tip_percent": tip_percent,
            "items": item_data
        })
        st.session_state.current_person_index += 1

# Step 3: PDF generation
if len(st.session_state.people_data) > 0 and st.button("Generate PDF Summary"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    grand_total = 0.0
    total_tip = 0.0
    total_item_cost = 0.0

    for person in st.session_state.people_data:
        pdf.set_font(style="B")
        pdf.cell(200, 10, f"{person['name']}", ln=True)
        pdf.set_font(style="")

        person_total = 0.0
        person_tip = 0.0
        for item in person["items"]:
            tax = item["price"] * st.session_state.tax_rate / 100
            tip = item["price"] * person["tip_percent"] / 100
            total = item["price"] + tax + tip
            pdf.cell(200, 10, f"{item['description']} - Price: ${item['price']:.2f}, Tax: ${tax:.2f}, Tip: ${tip:.2f}, Total: ${total:.2f}", ln=True)
            person_total += total
            person_tip += tip
            total_item_cost += item["price"]

        pdf.cell(200, 10, f"{person['name']}'s Total: ${person_total:.2f}", ln=True)
        pdf.ln()
        grand_total += person_total
        total_tip += person_tip

    pdf.set_font(style="B")
    pdf.cell(200, 10, f"GRAND TOTAL: ${grand_total:.2f}", ln=True)
    effective_tip = (total_tip / total_item_cost * 100) if total_item_cost > 0 else 0.0
    pdf.cell(200, 10, f"Effective Tip Percentage: {effective_tip:.2f}%", ln=True)

    output_path = "/mnt/data/simplified_bill_summary.pdf"
    pdf.output(output_path)
    st.success("PDF Generated!")
    st.download_button("Download PDF", data=open(output_path, "rb"), file_name="bill_summary.pdf")
