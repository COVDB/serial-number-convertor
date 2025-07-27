# serial-number-convertor

## Purpose
This Streamlit application merges three SAP Excel exports into a single report. It cleans the data, filters on a predefined equipment list and combines fields from AM LOG, ZSD\_PO\_PER\_SO and ZSTATUS files for easier analysis.

## Requirements
- Python 3.10 or newer
- Packages from `requirements.txt`

## Setup
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```
Launch the app in your browser using the URL printed by Streamlit.

## Example workflow
1. Upload the **AM LOG**, **ZSD\_PO\_PER\_SO** and **ZSTATUS** Excel files via the sidebar.
2. Click **Run Merge** to combine and filter the data.
3. Use the **Download merged Excel** button to save the results.

