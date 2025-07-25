import streamlit as st
import pandas as pd

st.set_page_config(page_title="Serial Number Merger", layout="centered")

st.title("Serial Number Merger")

st.write("""
1. Upload het **AM LOG EQUIPMENT LIST** bestand  
2. Upload het **Export** bestand  
3. Klik op 'Verwerken'  
""")

# Bestanden uploaden
amlog_file = st.file_uploader("Upload AM LOG EQUIPMENT LIST", type=["xlsx"])
export_file = st.file_uploader("Upload Export bestand", type=["xlsx"])

if amlog_file and export_file:
    try:
        # Inlezen met pandas
        df_amlog = pd.read_excel(amlog_file)
        df_export = pd.read_excel(export_file)

        st.success("Bestanden succesvol ingelezen!")

        # Kolommen tonen voor debug/controle
        with st.expander("Bekijk kolommen van AM LOG"):
            st.write(df_amlog.columns.tolist())
            st.dataframe(df_amlog.head())
        with st.expander("Bekijk kolommen van Export"):
            st.write(df_export.columns.tolist())
            st.dataframe(df_export.head())

        # Hier kunnen we straks verder bouwen!
    except Exception as e:
        st.error(f"Fout bij inlezen: {e}")
else:
    st.info("Upload beide bestanden om verder te gaan.")
