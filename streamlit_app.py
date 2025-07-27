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
    'Month of construction'
]

st.title("AM LOG Equipment Filter")

# Upload van het Excel-bestand
df = None
uploaded_file = st.file_uploader("Upload AM LOG Excel file", type=["xlsx", "xls"])
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Fout bij het lezen van het Excel-bestand: {e}")

if df is not None:
    # Zorg dat Material Number als string behandeld wordt
    df['Material Number'] = df['Material Number'].astype(str)
    # Filter de rijen
    filtered_df = df[df['Material Number'].isin(EQUIPMENT_NUMBERS)].copy()

    if filtered_df.empty:
        st.warning("Geen overeenkomende regels gevonden voor de opgegeven equipment nummers.")
    else:
        # Extract Year and Month from Delivery Date
        if 'Delivery Date' in filtered_df.columns:
            # Parse to datetime (format YYYY-MM-DD)
            filtered_df['Delivery Date'] = pd.to_datetime(filtered_df['Delivery Date'], errors='coerce')
            # Create construction year/month columns
            filtered_df['Year of construction'] = filtered_df['Delivery Date'].dt.year.fillna('').astype(str)
            filtered_df['Month of construction'] = filtered_df['Delivery Date'].dt.month.fillna('').astype(str).str.zfill(2)
        else:
            st.warning("Kolom 'Delivery Date' ontbreekt; kan geen bouwjaar/maand extraheren.")
            # Still add empty columns
            filtered_df['Year of construction'] = ''
            filtered_df['Month of construction'] = ''

        # Selecteer alleen de benodigde kolommen (controleer aanwezigheid)
        available_cols = [col for col in OUTPUT_COLUMNS if col in filtered_df.columns]
        missing_cols = set(OUTPUT_COLUMNS) - set(available_cols)
        if missing_cols:
            st.warning(f"De volgende kolommen ontbreken in het bestand en worden niet opgenomen: {', '.join(missing_cols)}")

        result_df = filtered_df[available_cols]
        st.success(f"Gevonden {len(result_df)} regels met de geselecteerde kolommen.")
        st.dataframe(result_df)

        # Maak een Excel-bestand in-memory met openpyxl
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False, sheet_name='Filtered')
        output.seek(0)

        # Download knop
        st.download_button(
            label="Download gefilterde resultaten als Excel",
            data=output,
            file_name="filtered_am_log.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
