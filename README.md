# Restaurant Bill Splitter

A Streamlit app that scans receipt images, parses items, and lets users assign items, tips, and tax per person. Exports to PDF (coming soon).

## Features
- OCR receipt parsing (Google Cloud Vision)
- Quantity toggle
- Item editing
- Multi-user assignment
- Per-person tax/tip
- Total calculator

## How to Run
```
pip install -r requirements.txt
streamlit run app.py
```