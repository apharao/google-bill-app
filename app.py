
import streamlit as st
from google.oauth2 import service_account
from google.cloud import vision
import io
import uuid

st.set_page_config(page_title="Restaurant Bill Splitter", layout="wide")

# --- Auth ---
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
)
client = vision.ImageAnnotatorClient(credentials=credentials)

# --- Helper to call OCR ---
def extract_text(image_bytes):
    image = vision.Image(content=image_bytes)
    response = client.document_text_detection(image=image)
    return response.full_text_annotation, response

# --- OCR Upload Step ---
st.title("📸 Restaurant Receipt OCR + Bill Splitter")
uploaded_file = st.file_uploader("Upload a restaurant receipt (JPG or PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image_bytes = uploaded_file.read()
    st.image(image_bytes, caption="Uploaded Receipt", use_container_width=True)

    with st.spinner("Extracting text..."):
        ocr_text, raw_response = extract_text(image_bytes)
        all_words = [word for page in raw_response.pages for block in page.blocks
                     for para in block.paragraphs for word in para.words]

    editable_text = st.text_area("📝 Editable OCR Text", value=ocr_text.text, height=300)

    # --- New Parsing Logic: Structured or Line-based ---
    fallback_to_lines = st.checkbox("Fallback to line-based parsing")
    st.markdown("↓ Parsed Items from OCR:")

    def parse_items_from_ocr(text, all_words, fallback=False):
        items = []
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        if fallback:
            st.write("⚠️ Forcing fallback to line-based parsing.")
            for line in lines:
                try:
                    if "-" in line:
                        parts = line.rsplit("-", 1)
                    else:
                        parts = line.rsplit(" ", 1)
                    if len(parts) == 2:
                        desc = parts[0].strip()
                        price = float(parts[1].replace("$", ""))
                        items.append({"id": str(uuid.uuid4()), "description": desc, "price": price})
                except:
                    pass
            return items

        # Attempt structured parsing
        header = None
        for line in lines[:5]:
            if "description" in line.lower() and "price" in line.lower():
                header = line
                break

        if not header:
            st.write("⚠️ No explicit header found. Attempting structured layout anyway...")

        # Convert all_words to dicts for processing
        word_dicts = []
        for word in all_words:
            text = "".join([s.text for s in word.symbols])
            x = sum([v.x for v in word.bounding_box.vertices]) / 4
            y = sum([v.y for v in word.bounding_box.vertices]) / 4
            word_dicts.append({"text": text, "x": x, "y": y})

        header_dicts = []
        if header:
            header_words = header.split()
            header_dicts = [{"text": h, "x": 0, "y": 0} for h in header_words]

        header_sorted = sorted(header_dicts, key=lambda w: w["x"]) if header_dicts else []

        if not header_sorted:
            header_sorted = [{"text": "Description", "x": 0}, {"text": "Qty", "x": 100}, {"text": "Price", "x": 200}]

        col_x = [w["x"] for w in header_sorted]

        rows = {}
        for word in word_dicts:
            y_key = round(word["y"] / 10) * 10
            rows.setdefault(y_key, []).append(word)

        for y, words in rows.items():
            row = ["", "", ""]
            for word in words:
                if len(col_x) >= 3:
                    if word["x"] < col_x[1]:
                        row[0] += word["text"] + " "
                    elif word["x"] < col_x[2]:
                        row[1] += word["text"] + " "
                    else:
                        row[2] += word["text"] + " "
            try:
                desc = row[0].strip()
                price = float(row[2].strip().replace("$", ""))
                items.append({"id": str(uuid.uuid4()), "description": desc, "price": price})
            except:
                continue

        return items

    parsed_items = parse_items_from_ocr(editable_text, all_words, fallback=fallback_to_lines)

    if parsed_items:
        for item in parsed_items:
            st.markdown(f"✅ **{item['description']}** - ${item['price']:.2f}")
    else:
        st.warning("⚠️ No items were parsed. Try editing the OCR text or enabling fallback mode.")
