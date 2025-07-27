import streamlit as st
import pandas as pd
import io

# Lijst met equipment nummers om te filteren
EQUIPMENT_NUMBERS = [
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

# Kolommen die we willen behouden in de output
OUTPUT_COLUMNS = [
    'Customer Reference',
    'Serial number',
    'Short text for sales order item',
    'Year of construction',
    'Month of construction',
    'Project Reference',  # vanuit tweede bestand
    'Material'            # vanuit tweede bestand
]

st.title("AM LOG Equipment Filter and Enrichment")

# 1. Upload AM LOG
st.header("1. Upload AM LOG Excel file")
df1 = None
file1 = st.file_uploader("Upload AM LOG", type=["xlsx", "xls"], key='am_log')
if file1:
    try:
        df1 = pd.read_excel(file1)
    except Exception as e:
        st.error(f"Fout bij het lezen van AM LOG: {e}")

# 2. Upload ZSD_PO_PER_SO
st.header("2. Upload ZSD_PO_PER_SO Excel file")
df2 = None
file2 = st.file_uploader("Upload ZSD_PO_PER_SO", type=["xlsx", "xls"], key='zsd')
if file2:
    try:
        df2 = pd.read_excel(file2)
        # Strip kolomnamen en whitespace
        df2.columns = df2.columns.str.strip()
        # Rename Purch.Doc. naar Customer Reference voor eenvoudiger merge
        if 'Purch.Doc.' in df2.columns:
            df2 = df2.rename(columns={'Purch.Doc.': 'Customer Reference'})
        else:
            st.error("Kolom 'Purch.Doc.' niet gevonden in ZSD_PO_PER_SO")
    except Exception as e:
        st.error(f"Fout bij het lezen van ZSD_PO_PER_SO: {e}")

# Verwerk wanneer beide bestanden zijn geüpload
if df1 is not None and df2 is not None:
    # Filter op materiaalnummer
    df1['Material Number'] = df1['Material Number'].astype(str).str.strip()
    filtered = df1[df1['Material Number'].isin(EQUIPMENT_NUMBERS)].copy()

    if filtered.empty:
        st.warning("Geen overeenkomende regels in AM LOG voor de opgegeven equipment nummers.")
    else:
        # Voeg bouwjaar en -maand toe
        if 'Delivery Date' in filtered.columns:
            filtered['Delivery Date'] = pd.to_datetime(filtered['Delivery Date'], errors='coerce')
            filtered['Year of construction'] = filtered['Delivery Date'].dt.year
            filtered['Month of construction'] = filtered['Delivery Date'].dt.month
        else:
            st.warning("Kolom 'Delivery Date' ontbreekt; bouwjaar/maand niet toe te voegen.")
            filtered['Year of construction'] = pd.NA
            filtered['Month of construction'] = pd.NA

        # Prepareer Customer Reference
        if 'Customer Reference' in filtered.columns:
            filtered['Customer Reference'] = filtered['Customer Reference'].astype(str).str.strip()
        else:
            st.error("Kolom 'Customer Reference' ontbreekt in AM LOG")

        # Merge met df2
        merged = pd.merge(
            filtered,
            df2[['Customer Reference', 'Project Reference', 'Material']],
            on='Customer Reference',
            how='left'
        )

        # Selecteer en toon result
        available = [col for col in OUTPUT_COLUMNS if col in merged.columns]
        result = merged[available]
        st.success(f"Resultaat: {len(result)} regels.")
        st.dataframe(result)

        # Exporteer naar Excel in-memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            result.to_excel(writer, index=False, sheet_name='Enriched')
        output.seek(0)
        st.download_button(
            label="Download resultaat als Excel",
            data=output,
            file_name="am_log_enriched.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
