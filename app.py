import streamlit as st
import uuid
from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image, ExifTags
import io
from fpdf import FPDF

# 🔐 Google credentials from st.secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
)

# 🔥 Confirm new parser is in use
def parse_items(text):
        st.markdown("🔥 **Running SMART parser with backtracking discount logic**")
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    items = []
    discount_keywords = ["discount", "happy hour"]

    st.markdown("### Debug: Parsed Lines")
    i = 0
    while i < len(lines):
        line = lines[i]

        try:
            # Try parsing as a float – this is the PRICE
            price = float(line.replace("$", "").replace(",", ""))
            if price < 0:
                # It's a discount, apply to previous item
                if items:
                    items[-1]["price"] += price  # price is negative
                    items[-1]["description"] += " (discount applied)"
                    st.text(f"Applied discount {price} to: {items[-1]}")
                else:
                    st.text(f"⚠️ Discount {price} found but no previous item to apply to")
                i += 1
                continue

            # Look backward for a valid description (skip quantities)
            j = i - 1
            while j >= 0:
                back_line = lines[j]
                try:
                    maybe_qty = float(back_line)
                    j -= 1
                except ValueError:
                    description = back_line
                    break
            else:
                description = f"Item {i}"  # fallback

            item = {
                "id": str(uuid.uuid4()),
                "description": description,
                "price": price
            }
            items.append(item)
            st.text(f"Matched: {item}")
            i += 1
        except ValueError:
            st.text(f"Skipped: {line}")
            i += 1

    return items
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    items = []
    skip_keywords = ["subtotal", "total", "tax", "tip", "change", "cash", "payment", "visa", "mastercard"]
    discount_keywords = ["discount", "happy hour"]

    st.markdown("### Debug: Parsed Lines")
    i = 0
    while i < len(lines) - 2:
        desc = lines[i]
        qty = lines[i + 1]  # ignored
        price = lines[i + 2]

        if any(k in desc.lower() for k in discount_keywords):
            st.text(f"Discount line detected: {desc}")
            if items:
                try:
                    discount = float(price.replace("$", "").replace(",", ""))
                    items[-1]["price"] += discount
                    items[-1]["description"] += " (discount applied)"
                    st.text(f"Applied discount {discount} to previous item: {items[-1]}")
                    i += 3
                    continue
                except ValueError:
                    st.text(f"Invalid discount price: {price}")
                    i += 1
                    continue
            else:
                st.text("Warning: discount appeared before any item")
                i += 1
                continue

        try:
            float_price = float(price.replace("$", "").replace(",", ""))
            item = {
                "id": str(uuid.uuid4()),
                "description": desc,
                "price": float_price
            }
            st.text(f"Matched: {item}")
            items.append(item)
            i += 3
        except ValueError:
            st.text(f"No match: {desc}, {qty}, {price}")
            i += 1

    return items

def extract_text_from_image(uploaded_image):
    image = Image.open(uploaded_image)
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(image._getexif().items())
        orientation = exif.get(orientation, 1)
        if orientation == 3:
            image = image.rotate(180, expand=True)
        elif orientation == 6:
            image = image.rotate(270, expand=True)
        elif orientation == 8:
            image = image.rotate(90, expand=True)
    except:
        pass

    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    content = buffer.getvalue()

    client = vision.ImageAnnotatorClient(credentials=credentials)
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    return texts[0].description if texts else ""

# App layout
st.title("🧾 Google OCR Bill Splitter")
uploaded_file = st.file_uploader("Upload a receipt image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    raw_text = extract_text_from_image(uploaded_file)
    editable_text = st.text_area("✏️ Review and edit OCR text below:", raw_text, height=300)

    if st.button("Parse Items"):
        st.session_state.parsed_items = parse_items(editable_text)

if "parsed_items" in st.session_state:
    st.subheader("Parsed Items")
    if st.session_state.parsed_items:
        for item in st.session_state.parsed_items:
            st.write(f"{item['description']} - ${item['price']:.2f}")
    else:
        st.warning("No items were parsed. Check the debug output above.")
