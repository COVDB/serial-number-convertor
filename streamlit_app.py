import streamlit as st
import pandas as pd
import io

# Lijst met equipment nummers om te filteren
equipment_numbers = [
    '000000000001001917', '000000000001001808', '000000000001001749',
    '000000000001001776', '000000000001001911', '000000000001001755',
    '000000000001001760', '000000000001001809', '000000000001001747',
    '000000000001001711', '000000000001001757', '000000000001001708',
    '000000000001001770', '000000000001001710', '000000000001001771',
    '000000000001001758', '000000000001007905', '000000000001001753',
    '000000000001001752', '000000000001008374', '000000000001001805',
    '000000000001001709', '000000000001008561', '000000000001008560',
    '000000000001001765', '000000000001001775', '000000000001009105',
    '000000000001001777', '000000000001001742', '000000000001001813',
    '000000000001009719'
]

# Output kolommen
def get_output_columns():
    return [
        'Customer Reference',
        'Serial number',
        'Short text for sales order item',
        'Year of construction',
        'Month of construction',
        'Document',
        'Material'
    ]

st.title("AM LOG Filter & Enrichment")

# 1. Upload AM LOG
st.header("1. Upload AM LOG Excel file")
df1 = None
file1 = st.file_uploader("AM LOG (xlsx/xls)", type=["xlsx", "xls"], key='am_log')
if file1:
    try:
        df1 = pd.read_excel(file1)
        df1.columns = df1.columns.str.strip()
    except Exception as e:
        st.error(f"Fout bij lezen AM LOG: {e}")

# 2. Upload ZSD_PO_PER_SO
st.header("2. Upload ZSD_PO_PER_SO Excel file")
df2 = None
file2 = st.file_uploader("ZSD_PO_PER_SO (xlsx/xls)", type=["xlsx", "xls"], key='zsd')
if file2:
    try:
        df2 = pd.read_excel(file2)
        df2.columns = df2.columns.str.strip()
        # Rename Purch.Doc or Purch.Doc. to Customer Reference
        if 'Purch.Doc.' in df2.columns:
            df2 = df2.rename(columns={'Purch.Doc.': 'Customer Reference'})
        elif 'Purch.Doc' in df2.columns:
            df2 = df2.rename(columns={'Purch.Doc': 'Customer Reference'})
        else:
            st.error("Kolom 'Purch.Doc' niet gevonden in ZSD_PO_PER_SO")
    except Exception as e:
        st.error(f"Fout bij lezen ZSD_PO_PER_SO: {e}")

# Verwerk wanneer beide datasets aanwezig zijn
if df1 is not None and df2 is not None:
    # Keys standaardiseren
    df1 = df1.copy()
    df1['Customer Reference'] = df1.get('Customer Reference', pd.Series(dtype=str)).astype(str).str.strip()
    df2['Customer Reference'] = df2['Customer Reference'].astype(str).str.strip()

    # Filter op equipment numbers
    df1['Material Number'] = df1.get('Material Number', pd.Series(dtype=str)).astype(str).str.strip()
    filtered = df1[df1['Material Number'].isin(equipment_numbers)].copy()

    if filtered.empty:
        st.warning("Geen AM LOG regels voor opgegeven equipment nummers.")
    else:
        # Bouwjaar/maand uit Delivery Date
        if 'Delivery Date' in filtered.columns:
            filtered['Delivery Date'] = pd.to_datetime(filtered['Delivery Date'], errors='coerce')
            filtered['Year of construction'] = filtered['Delivery Date'].dt.year
            filtered['Month of construction'] = filtered['Delivery Date'].dt.month
        else:
            filtered['Year of construction'] = pd.NA
            filtered['Month of construction'] = pd.NA

        # Merge op Customer Reference met Document en Material
        merged = pd.merge(
            filtered,
            df2[['Customer Reference', 'Document', 'Material']],
            on='Customer Reference',
            how='left'
        )

        # Resultaat tonen en exporteren
        cols = [c for c in get_output_columns() if c in merged.columns]
        result = merged[cols]
        st.success(f"Resultaat: {len(result)} regels.")
        st.dataframe(result)

        # Excel export
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            result.to_excel(writer, index=False, sheet_name='Enriched')
        output.seek(0)
        st.download_button(
            "Download Excel",
            data=output,
            file_name="am_log_enriched.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
