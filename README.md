# Restaurant Bill Splitter with Structured OCR

This Streamlit app uses Google Cloud Vision to OCR restaurant receipts and intelligently split the bill.

## Features
- Upload images (JPG/PNG) of receipts
- Use bounding box data to parse column-aligned items like Description, Qty, Price
- Support discounts, duplicate item names, and item editing
- Assign items per person, calculate tax and tip
- Export summary to PDF

## How to Use
1. Upload your Google Vision API credentials as `GOOGLE_APPLICATION_CREDENTIALS_JSON` in Streamlit secrets
2. Run the app on Streamlit Cloud or locally
3. Upload a receipt image and parse the structured columns

## License
Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International
