
import streamlit as st
import json
from google.oauth2 import service_account
from google.cloud import vision
import uuid
import re

# Load Google credentials properly
service_account_info = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
credentials = service_account.Credentials.from_service_account_info(service_account_info)
client = vision.ImageAnnotatorClient(credentials=credentials)

st.title("Restaurant Bill Splitter (Google Vision OCR)")

uploaded_file = st.file_uploader("Upload a receipt image", type=["jpg", "jpeg", "png"])
use_quantity = st.checkbox("Does the bill include quantities?", value=True)

if uploaded_file:
    from PIL import Image, ExifTags
    image = Image.open(uploaded_file)
    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation] == 'Orientation':
            break
    try:
        exif = dict(image._getexif().items())
        if exif[orientation] == 3:
            image = image.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image = image.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image = image.rotate(90, expand=True)
    except:
        pass

    st.image(image, caption="Uploaded Receipt", use_container_width=True)
    image.save("temp.png")

    with open("temp.png", "rb") as img_file:
        content = img_file.read()
    image_for_ocr = vision.Image(content=content)
    response = client.text_detection(image=image_for_ocr)
    texts = response.text_annotations

    if texts:
        full_text = texts[0].description
        st.text_area("Editable OCR Text", value=full_text, height=300, key="ocr_text")

        if st.button("Parse Items"):
            lines = [line.strip() for line in full_text.split("\n") if line.strip()]
            parsed_items = []
            for line in lines:
                match = re.match(r"^(.*?)(?:\s+\d+(?:\.\d{1,2})?)?\s+(\$?-?\d+(\.\d{2})?)$", line)
                if match:
                    desc = match.group(1).strip()
                    price = float(match.group(2).replace("$", "").replace(",", ""))
                    parsed_items.append({"id": str(uuid.uuid4()), "description": desc, "price": price})
            st.session_state.parsed_items = parsed_items
            st.write("Parsed items updated.")

if "parsed_items" in st.session_state:
    st.subheader("Parsed Items")
    for item in st.session_state.parsed_items:
        st.write(f"{item['description']} - ${item['price']:.2f}")
