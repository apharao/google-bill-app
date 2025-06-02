# Restaurant Bill Splitter with OCR

A Streamlit app that uses Google Cloud Vision to scan restaurant receipts and parse them into billable items.

## Features
- Upload and OCR receipt images
- Edit OCR text
- Parse items into descriptions and prices
- Assign unique IDs to handle duplicates

## Setup

Make sure to add your Google Cloud credentials in `.streamlit/secrets.toml` under:

```toml
GOOGLE_APPLICATION_CREDENTIALS_JSON = """<YOUR JSON KEY CONTENT>"""
```