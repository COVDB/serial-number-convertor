import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Serial Number Merger", layout="centered")
st.title("Serial Number Merger")

st.write("""
1. Upload het **AM LOG EQUIPMENT LIST** bestand  
2. Upload het **Export** bestand  
3. Upload de **ZSTATUS** export file  
4. Selecteer in welke kolommen de keys staan  
5. Klik op **Verwerken** om alles te mergen  
""")

# 1) Uploader
amlog_file   = st.file_uploader("1) AM LOG (.xlsx)",   type="xlsx")
export_file  = st.file_uploader("2) Export (.xlsx)",     type="xlsx")
zstatus_file = st.file_uploader("3) ZSTATUS (.xlsx)",    type="xlsx")

if amlog_file and export_file and zstatus_file:
    try:
        # 2) Inlezen
        df_amlog   = pd.read_excel(amlog_file)
        df_export  = pd.read_excel(export_file)
        df_zstatus = pd.read_excel(zstatus_file)
        st.success("Bestanden ingelezen!")

        # 3) Kolomselectie voor de merges
        st.subheader("Selecteer de merge‐kolommen")

        amlog_ref       = st.selectbox("AM LOG: Customer Reference", df_amlog.columns)
        export_purch    = st.selectbox("EXPORT: Purch.Doc",           df_export.columns)
        export_project  = st.selectbox("EXPORT: Project Reference",   df_export.columns)
        zstatus_projref = st.selectbox("ZSTATUS: ProjRef",            df_zstatus.columns)

        # 4) Optioneel: extra kolommen uit AM LOG om later weer te geven
        amlog_eq    = st.selectbox("AM LOG: Equipment Number", df_amlog.columns)
        amlog_sn    = st.selectbox("AM LOG: Serial Number",    df_amlog.columns)

        if st.button("Verwerken"):
            # 5) Clean keys: zorg dat het allemaal strings zijn zonder '.0'
            def clean_col(df, col):
                df[col] = (df[col]
                           .astype(str)
                           .str.replace(r'\.0$', '', regex=True)
                           .str.strip())
            clean_col(df_amlog, amlog_ref)
            clean_col(df_export, export_purch)
            clean_col(df_export, export_project)
            clean_col(df_zstatus, zstatus_projref)

            # 6) Eerste merge: AM LOG ↔ EXPORT
            df12 = pd.merge(
                df_amlog,
                df_export,
                left_on=amlog_ref,
                right_on=export_purch,
                how="left",
                suffixes=("_amlog","_exp")
            )
            st.write(f"Na eerste merge: {len(df12)} rijen")

            # 7) Tweede merge: ↔ ZSTATUS
            df123 = pd.merge(
                df12,
                df_zstatus,
                left_on=export_project,
                right_on=zstatus_projref,
                how="left",
                suffixes=("","_zst")
            )
            st.write(f"Na tweede merge: {len(df123)} rijen")

            # 8) Preview en download
            st.dataframe(df123[[amlog_ref, amlog_eq, amlog_sn, export_project]].head(100))

            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df123.to_excel(writer, index=False, sheet_name="Merged")
            st.download_button(
                label="Download merged Excel",
                data=buf.getvalue(),
                file_name="merged_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Er ging iets mis: {e}")
else:
    st.info("Upload alle drie de bestanden om verder te gaan.")
