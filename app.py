import streamlit as st
from google.cloud import vision
from google.oauth2 import service_account
import io
from PIL import Image
import uuid

# Load credentials from Streamlit secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
)

client = vision.ImageAnnotatorClient(credentials=credentials)

st.title("📷 Restaurant Bill Splitter (Structured OCR Mode)")

uploaded_file = st.file_uploader("Upload receipt image", type=["png", "jpg", "jpeg"])
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded receipt", use_container_width=True)

    # Read image bytes
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

    # Cluster into rows based on y-axis
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

    # Attempt to identify header row
    header = None
    for row in rows:
        joined = ' '.join([w["text"].lower() for w in row])
        if "description" in joined and "price" in joined:
            header = row
            break

    if header:
        st.success("Table header detected. Parsing structured rows...")
        # Estimate column x-positions
        header_sorted = sorted(header, key=lambda w: w["x"])
        col_x = [w["x"] for w in header_sorted]
        col_labels = [w["text"].lower() for w in header_sorted]

        def get_column(x):
            distances = [abs(x - cx) for cx in col_x]
            return col_labels[distances.index(min(distances))]

        # Build item list
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
            st.warning("No items parsed. Try re-scanning or use fallback mode.")
        else:
            for item in items:
                st.write(f'{item["description"]} - ${item["price"]:.2f}')
    else:
        st.error("Could not detect table header. Consider enabling fallback mode or using a clearer receipt image.")
