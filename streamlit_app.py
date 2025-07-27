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
def get_output_columns():
    return [
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
file1 = st.file_uploader("Upload AM LOG (xlsx/xls)", type=["xlsx", "xls"], key='am_log')
if file1 is not None:
    try:
        df1 = pd.read_excel(file1)
        df1.columns = df1.columns.str.strip()
        st.write("AM LOG preview:", df1.head())
    except Exception as e:
        st.error(f"Fout bij het lezen van AM LOG: {e}")

# 2. Upload ZSD_PO_PER_SO
st.header("2. Upload ZSD_PO_PER_SO Excel file")
df2 = None
file2 = st.file_uploader("Upload ZSD_PO_PER_SO (xlsx/xls)", type=["xlsx", "xls"], key='zsd')
if file2 is not None:
    try:
        df2 = pd.read_excel(file2)
        df2.columns = df2.columns.str.strip()
        st.write("ZSD_PO_PER_SO preview:", df2.head())
        # Rename Purch.Doc or Purch.Doc. to Customer Reference for merge
        if 'Purch.Doc.' in df2.columns:
            df2 = df2.rename(columns={'Purch.Doc.': 'Customer Reference'})
        elif 'Purch.Doc' in df2.columns:
            df2 = df2.rename(columns={'Purch.Doc': 'Customer Reference'})
        else:
            st.error("Kolom 'Purch.Doc.' of 'Purch.Doc' niet gevonden in ZSD_PO_PER_SO.")
        df2['Customer Reference'] = df2['Customer Reference'].astype(str).str.strip()
    except Exception as e:
        st.error(f"Fout bij het lezen van ZSD_PO_PER_SO: {e}")

# 3. Verwerk en merge
if df1 is not None and df2 is not None:
    # Filter op equipment nummers
    df1['Material Number'] = df1['Material Number'].astype(str).str.strip()
    filtered = df1[df1['Material Number'].isin(EQUIPMENT_NUMBERS)].copy()

    if filtered.empty:
        st.warning("Geen overeenkomende regels in AM LOG voor de opgegeven equipment nummers.")
    else:
        # Extract Year and Month from Delivery Date
        if 'Delivery Date' in filtered.columns:
            filtered['Delivery Date'] = pd.to_datetime(filtered['Delivery Date'], errors='coerce')
            filtered['Year of construction'] = filtered['Delivery Date'].dt.year.astype('Int64')
            filtered['Month of construction'] = filtered['Delivery Date'].dt.month.astype('Int64')
        else:
            st.warning("Kolom 'Delivery Date' ontbreekt; geen bouwjaar/maand.")
            filtered['Year of construction'] = pd.NA
            filtered['Month of construction'] = pd.NA

        # Merge met tweede bestand op Customer Reference
        merged = pd.merge(
            filtered,
            df2[['Customer Reference', 'Project Reference', 'Material']],
            how='left',
            left_on='Customer Reference',
            right_on='Customer Reference',
            indicator=True
        )
        st.write("Merge status:", merged['_merge'].value_counts())

        # Toon enkele matched records
        matches = merged[merged['_merge'] == 'both']
        if not matches.empty:
            st.write("Enkele matched records:", matches[['Customer Reference', 'Project Reference', 'Material']].head())
        else:
            st.error("Geen overeenkomstige Customer References gevonden in ZSD_PO_PER_SO.")

        # Selecteer en toon alleen benodigde kolommen
        available = [col for col in get_output_columns() if col in merged.columns]
        missing = set(get_output_columns()) - set(available)
        if missing:
            st.warning(f"Ontbrekende kolommen en niet getoond: {', '.join(missing)}")

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
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key='download'
        )
