import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Serial Number Merger", layout="centered")
st.title("Serial Number Merger")

st.write("""
1. Upload het **AM LOG EQUIPMENT LIST** bestand  
2. Upload het **Export** bestand  
3. Selecteer de juiste kolommen  
4. Klik op 'Verwerken'
""")

amlog_file = st.file_uploader("Upload AM LOG EQUIPMENT LIST", type=["xlsx"])
export_file = st.file_uploader("Upload Export bestand", type=["xlsx"])

if amlog_file and export_file:
    try:
        df_amlog = pd.read_excel(amlog_file)
        df_export = pd.read_excel(export_file)

        st.success("Bestanden ingelezen!")

        st.write("**Stap 1: Selecteer de kolommen voor AM LOG**")
        amlog_cols = df_amlog.columns.tolist()
        amlog_ref_col = st.selectbox("Customer Reference (AM LOG)", amlog_cols)
        amlog_eq_col = st.selectbox("Equipment Number (AM LOG)", amlog_cols)
        amlog_sn_col = st.selectbox("Serial Number (AM LOG)", amlog_cols)

        st.write("**Stap 2: Selecteer de kolommen voor EXPORT**")
        export_cols = df_export.columns.tolist()
        export_ref_col = st.selectbox("Purch.Doc (EXPORT)", export_cols)
        export_proj_col = st.selectbox("Project Reference (EXPORT)", export_cols)
        export_doc_col = st.selectbox("Document (EXPORT)", export_cols)
        export_mat_col = st.selectbox("Material (EXPORT)", export_cols)
        export_sold_col = st.selectbox("Sold-to party (EXPORT)", export_cols)
        export_desc_col = st.selectbox("Description (EXPORT)", export_cols)

        if st.button("Verwerken"):
            # Alleen relevante kolommen selecteren
            amlog_sel = df_amlog[[amlog_ref_col, amlog_eq_col, amlog_sn_col]]
            export_sel = df_export[[export_proj_col, export_doc_col, export_mat_col, export_sold_col, export_desc_col, export_ref_col]]
            
            # Zet beide merge-kolommen expliciet om naar string/tekst
            amlog_sel[amlog_ref_col] = amlog_sel[amlog_ref_col].astype(str).str.strip()
            export_sel[export_ref_col] = export_sel[export_ref_col].astype(str).str.strip()

            # Merge op referentie
            merged = pd.merge(
                amlog_sel,
                export_sel,
                left_on=amlog_ref_col,
                right_on=export_ref_col,
                how="left"
            )

            # Kolommen volgorde output
            output_cols = [
                export_proj_col, export_doc_col, export_mat_col, export_sold_col, export_desc_col, export_ref_col,
                amlog_eq_col, amlog_sn_col
            ]
            merged = merged[output_cols]

            st.success(f"Samengevoegd! {len(merged)} rijen in output.")
            st.dataframe(merged.head(100))

            # Download als Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                merged.to_excel(writer, index=False, sheet_name="Merged")
            st.download_button(
                label="Download resultaat als Excel",
                data=output.getvalue(),
                file_name="merged_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"Fout bij verwerken: {e}")
else:
    st.info("Upload beide bestanden om verder te gaan.")
