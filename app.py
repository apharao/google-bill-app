
import streamlit as st
import requests
import json
import base64
from google.oauth2 import service_account
from google.cloud import vision
from PIL import Image, ImageOps, ExifTags
import io
from fpdf import FPDF
import uuid

st.set_page_config(layout="wide")
st.title("📸 Smart Bill Splitter with Google OCR")

# Setup Google Cloud Vision credentials from Streamlit secrets
credentials_info = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
credentials = service_account.Credentials.from_service_account_info(credentials_info)
client = vision.ImageAnnotatorClient(credentials=credentials)

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

def extract_text_google_vision(uploaded_file):
    image_bytes = uploaded_file.read()
    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description
    else:
        return ""

# Init session state
for key in ["raw_text", "receipt_items", "item_id_map", "people", "claimed"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key == "raw_text" else ([] if key in ["receipt_items", "people", "claimed"] else {})

st.markdown("### Step 1: Upload a receipt image")
uploaded_file = st.file_uploader("Choose image", type=["jpg", "jpeg", "png"])
if uploaded_file and not st.session_state.raw_text:
    image = Image.open(uploaded_file)
    image = fix_orientation(image)
    st.image(image, caption="Uploaded Receipt", use_container_width=True)
    st.session_state.raw_text = extract_text_google_vision(uploaded_file)

if st.session_state.raw_text:
    st.markdown("### Step 2: OCR Extracted Text")
    st.text_area("OCR Text", st.session_state.raw_text, height=300)
    st.markdown("⬆️ Edit above before continuing if needed.")

# Placeholder for full item parsing, selection, tax/tip input, assignment, and PDF generation
st.info("Full assignment, checkbox logic, and PDF generation continues from here.")
