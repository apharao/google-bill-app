
import streamlit as st
from uuid import uuid4

st.set_page_config(page_title="Restaurant Bill Splitter", layout="wide")

# Dummy OCR parsed output for demo purposes
if "parsed_items" not in st.session_state:
    st.session_state.parsed_items = [
        {"id": str(uuid4()), "description": "Dos Hombres Mezcal", "price": 9.99},
        {"id": str(uuid4()), "description": "Discount During Happy Hour", "price": -2.00},
        {"id": str(uuid4()), "description": "Margarita", "price": 2.00},
        {"id": str(uuid4()), "description": "HH Chicken Lettuce Wraps", "price": 7.75},
        {"id": str(uuid4()), "description": "HH Fried Chicken Tenders", "price": 7.50},
    ]

if "assigned_items" not in st.session_state:
    st.session_state.assigned_items = {}

st.title("Restaurant Bill Splitter")

st.subheader("Step 1: Edit Items (if needed)")
updated_items = []
for item in st.session_state.parsed_items:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text(item["description"])
    with col2:
        price = st.text_input(f"Edit price for {item['description']}", value=str(item["price"]), key=f"price_{item['id']}")
    item["price"] = float(price)
    updated_items.append(item)
st.session_state.parsed_items = updated_items

st.divider()
st.subheader("Step 2: Assign Items to Person")
person_name = st.text_input("Enter person’s name")

if person_name:
    unassigned_items = [item for item in st.session_state.parsed_items if item["id"] not in st.session_state.assigned_items]
    selected_ids = st.multiselect("Select items to assign", [f"{item['description']} - ${item['price']}" for item in unassigned_items])

    if st.button("Assign Selected Items"):
        for label in selected_ids:
            for item in unassigned_items:
                full_label = f"{item['description']} - ${item['price']}"
                if full_label == label:
                    st.session_state.assigned_items[item["id"]] = person_name
        st.success(f"Assigned selected items to {person_name}")

st.divider()
st.subheader("Currently Assigned Items")
for item in st.session_state.parsed_items:
    if item["id"] in st.session_state.assigned_items:
        st.markdown(f"~~{item['description']} - ${item['price']}~~ → {st.session_state.assigned_items[item['id']]}")
    else:
        st.markdown(f"{item['description']} - ${item['price']}")
