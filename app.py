import streamlit as st
from google.cloud import vision
from google.oauth2 import service_account
import json
import io
from PIL import Image
import uuid

# Load credentials
credentials = service_account.Credentials.from_service_account_info(
    json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
)

client = vision.ImageAnnotatorClient(credentials=credentials)

st.title("📷 Restaurant Bill Splitter (Structured OCR Mode)")

uploaded_file = st.file_uploader("Upload receipt image", type=["png", "jpg", "jpeg"])
force_mode = st.checkbox("Force structured parsing if header not found")

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded receipt", use_container_width=True)

    content = uploaded_file.read()
    image_context = vision.Image(content=content)
    response = client.document_text_detection(image=image_context)

    words = []
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    text = ''.join([symbol.text for symbol in word.symbols])
                    vertices = word.bounding_box.vertices
                    x = int(sum([v.x for v in vertices]) / 4)
                    y = int(sum([v.y for v in vertices]) / 4)
                    words.append({"text": text, "x": x, "y": y})

    # Sort by y then x
    words.sort(key=lambda w: (w["y"], w["x"]))

    # Group into rows
    rows = []
    current_row = []
    threshold = 15
    for word in words:
        if not current_row:
            current_row.append(word)
            continue
        if abs(word["y"] - current_row[-1]["y"]) < threshold:
            current_row.append(word)
        else:
            rows.append(current_row)
            current_row = [word]
    if current_row:
        rows.append(current_row)

    # Detect header row
    header = None
    for row in rows:
        joined = ' '.join([w["text"].lower() for w in row])
        if "description" in joined and "price" in joined:
            header = row
            break

    if header or force_mode:
        st.success("Table header detected. Parsing structured rows..." if header else "Forcing structured parsing without header...")

        # Convert Vision header to dicts if needed
        if header and not isinstance(header[0], dict):
            header_dicts = []
            for w in header:
                text = ''.join([s.text for s in w.symbols])
                vertices = w.bounding_box.vertices
                x = int(sum(v.x for v in vertices) / 4)
                y = int(sum(v.y for v in vertices) / 4)
                header_dicts.append({"text": text, "x": x, "y": y})
            header_sorted = sorted(header_dicts, key=lambda w: w["x"])
        else:
            header_sorted = sorted(header, key=lambda w: w["x"])

        col_x = [w["x"] for w in header_sorted]
        col_labels = [w["text"].lower() for w in header_sorted]

        def get_column(x):
            distances = [abs(x - cx) for cx in col_x]
            return col_labels[distances.index(min(distances))]

        items = []
        for row in rows:
            if row == header or len(row) < 2:
                continue
            cols = {"description": "", "qty": "", "price": ""}
            for word in row:
                col = get_column(word["x"])
                if col in cols:
                    cols[col] += word["text"] + " "
            try:
                price = float(cols["price"].strip())
                desc = cols["description"].strip()
                items.append({
                    "id": str(uuid.uuid4()),
                    "description": desc,
                    "price": price
                })
            except:
                continue

        st.subheader("🧾 Parsed Items")
        if not items:
            st.warning("No items parsed. Try fallback mode or clearer receipt.")
        else:
            for item in items:
                st.write(f'{item["description"]} - ${item["price"]:.2f}')
    else:
        st.error("Could not detect table header. Try enabling fallback mode or uploading a clearer image.")
