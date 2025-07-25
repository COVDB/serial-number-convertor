import streamlit as st
import pandas as pd
import io

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

        # Toon de kolomnamen
        with st.expander("AM LOG kolommen"):
            st.write(df_amlog.columns.tolist())
        with st.expander("Export kolommen"):
            st.write(df_export.columns.tolist())
        
        # (Aanpasbaar: indien kolomnamen verschillen per export)
        # Gebruik lower case kolomnamen voor robuustheid
        df_amlog.columns = [c.lower().strip() for c in df_amlog.columns]
        df_export.columns = [c.lower().strip() for c in df_export.columns]

        # Mapping van kolomnamen
        amlog_ref_col = "customer reference"
        amlog_eq_col = "equipment number"
        amlog_sn_col = "serial number"
        
        export_ref_col = "purch.doc"
        export_proj_col = "project reference"
        export_doc_col = "document"
        export_mat_col = "material"
        export_sold_col = "sold-to party"
        export_desc_col = "description"

        # Alleen relevante kolommen selecteren
        amlog_sel = df_amlog[[amlog_ref_col, amlog_eq_col, amlog_sn_col]]
        export_sel = df_export[[export_proj_col, export_doc_col, export_mat_col, export_sold_col, export_desc_col, export_ref_col]]

        # Merge op: amlog customer reference ↔ export purch.doc
        merged = pd.merge(
            amlog_sel,
            export_sel,
            left_on=amlog_ref_col,
            right_on=export_ref_col,
            how="left"
        )

        # Optioneel: Kolommen in gewenste volgorde
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

