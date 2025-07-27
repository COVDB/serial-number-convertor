import streamlit as st
import pandas as pd

# List of equipment numbers to filter
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

st.title("AM LOG Equipment Filter")

uploaded_file = st.file_uploader("Upload AM LOG Excel file", type=["xlsx", "xls"])
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Fout bij het lezen van het Excel-bestand: {e}")
    else:
        # Ensure 'Material Number' is string type
        df['Material Number'] = df['Material Number'].astype(str)
        # Filter rows
        filtered_df = df[df['Material Number'].isin(EQUIPMENT_NUMBERS)]

        if filtered_df.empty:
            st.warning("Geen overeenkomende regels gevonden voor de opgegeven equipment nummers.")
        else:
            st.success(f"Gevonden {len(filtered_df)} regels.")
            st.dataframe(filtered_df)

            # Offer download of filtered results
            towrite = pd.ExcelWriter("filtered_am_log.xlsx", engine='xlsxwriter')
            filtered_df.to_excel(towrite, index=False, sheet_name='Filtered')
            towrite.save()

            with open("filtered_am_log.xlsx", "rb") as f:
                st.download_button(
                    label="Download gefilterde resultaten als Excel",
                    data=f,
                    file_name="filtered_am_log.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
