
import streamlit as st
import uuid

# Utility to initialize state
if "assigned_items" not in st.session_state:
    st.session_state.assigned_items = {}

# Header
st.header("Assign Items to People")

# Unique people tracker
if "people" not in st.session_state:
    st.session_state.people = []

# Add new person
with st.form("add_person_form"):
    new_person = st.text_input("Enter person's name")
    submitted = st.form_submit_button("Add Person")
    if submitted and new_person:
        if new_person not in st.session_state.people:
            st.session_state.people.append(new_person)

# Display assignment form for each person
for person in st.session_state.people:
    st.subheader(f"Items for {person}")
    with st.expander("Assign items", expanded=True):
        assigned = st.multiselect(
            f"Select items for {person}",
            [item["description"] for item in st.session_state.items if item["id"] not in st.session_state.assigned_items],
            key=f"selection_{person}",
        )
        if st.button(f"Confirm Selection for {person}"):
            for desc in assigned:
                for item in st.session_state.items:
                    if item["description"] == desc and item["id"] not in st.session_state.assigned_items:
                        st.session_state.assigned_items[item["id"]] = person
                        break

# Display summary
st.subheader("Assignment Summary")
for item in st.session_state.items:
    owner = st.session_state.assigned_items.get(item["id"], "Unassigned")
    st.write(f"{item['description']} - ${item['price']} → **{owner}**")
