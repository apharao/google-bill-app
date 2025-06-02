
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
if "current_items" not in st.session_state:
    st.session_state.current_items = []

# Buffer fields for new item entry
if "item_description" not in st.session_state:
    st.session_state.item_description = ""
if "item_price" not in st.session_state:
    st.session_state.item_price = 0.0

st.title("Bill Splitter with Tax & Tip")

# Step 1: Set tax rate once
if st.session_state.current_person_index == 0 and not st.session_state.people_data:
    st.session_state.tax_rate = st.number_input("Enter tax rate (%) for everyone", min_value=0.0, step=0.01)

# Step 2: Per person input
st.header(f"Person #{st.session_state.current_person_index + 1}")

with st.form("person_form", clear_on_submit=False):
    name = st.text_input("Enter person's name")
    tip_percent = st.number_input("Enter tip percentage for this person", min_value=0.0, step=0.01)

    desc = st.text_input("Item description", key="item_description", placeholder="e.g. Tacos", label_visibility="visible")
    price = st.number_input("Item price", step=0.01, key="item_price")

    col1, col2 = st.columns(2)
    add_item = col1.form_submit_button("Add Item")
    finalize = col2.form_submit_button("Finalize Person")

    if add_item:
        if desc and price > 0:
            st.session_state.current_items.append({"description": desc, "price": price})
            st.session_state.item_description = ""
            st.session_state.item_price = 0.0
            st.rerun()

    if finalize and name and st.session_state.current_items:
        st.session_state.people_data.append({
            "name": name,
            "tip_percent": tip_percent,
            "items": st.session_state.current_items.copy()
        })
        st.session_state.current_person_index += 1
        st.session_state.current_items.clear()
        st.session_state.item_description = ""
        st.session_state.item_price = 0.0
        st.rerun()


# Show live items with edit/delete
if st.session_state.current_items:
    st.subheader("Current Items for This Person")
    for i, item in enumerate(st.session_state.current_items):
        col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
        new_desc = col1.text_input(f"Description {i}", item["description"], key=f"edit_desc_{i}")
        new_price = col2.number_input(f"Price {i}", value=item["price"], step=0.01, key=f"edit_price_{i}")
        update = col3.button("Update", key=f"update_{i}")
        delete = col4.button("🗑", key=f"delete_{i}")
        if update:
            st.session_state.current_items[i] = {"description": new_desc, "price": new_price}
            st.rerun()
        if delete:
            del st.session_state.current_items[i]
            st.rerun()

# Show live items
if st.session_state.current_items:
    st.subheader("Current Items for This Person")
    for i, item in enumerate(st.session_state.current_items, 1):
        st.markdown(f"**{i}.** {item['description']} - ${item['price']:.2f}")

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

    output_path = "/mnt/data/simplified_dynamic_bill_summary_resetfix.pdf"
    pdf.output(output_path)
    st.success("PDF Generated!")
    st.download_button("Download PDF", data=open(output_path, "rb"), file_name="bill_summary.pdf")
