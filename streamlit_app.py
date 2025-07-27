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
5. Plak in de tekstbox de material‐codes (één per regel)  
6. Klik op **Verwerken** om te mergen én direct te filteren op Material  
""")

# 1) Upload
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

        # 3) Kolomselectie
        st.subheader("Selecteer de key‐kolommen")

        amlog_ref       = st.selectbox("AM LOG: Customer Reference",   df_amlog.columns)
        export_purch    = st.selectbox("EXPORT: Purch.Doc",             df_export.columns)
        export_project  = st.selectbox("EXPORT: Project Reference",     df_export.columns)
        zstatus_projref = st.selectbox("ZSTATUS: ProjRef",              df_zstatus.columns)

        # 4) Kolomselectie serial/equipment (optioneel)
        amlog_eq = st.selectbox("AM LOG: Equipment Number", df_amlog.columns)
        amlog_sn = st.selectbox("AM LOG: Serial Number",    df_amlog.columns)

        # 5) Material‐filterlijst
        st.subheader("Filter op materiaal‐referenties")
        FILTER_MATERIALS = st.text_area(
            "Plak hier jouw material codes, één per regel",
            value="\n".join([
                "ATL3.3_12X8C",
                "ATL3.3_12X10C",
                "ATL3.3_12X10N",
                "ATL3.3_12X10NM/H",
                "ATL3.3_10X12N UL",
                "ATL3.2_12X8C",
                "ATL3.3_116X116C",
                "ATL3.3_12X8NM/H",
                "ATL3.3_12X10N/H",
                "ATL3.3_12X8N",
                "ATL3.2_12X10N",
                "ATL3.3_12X12N",
                "ATL3.2_12X10N/H",
                "ATL3.3_12X8NM",
                "ATL3.3_12X12N UL",
                "ATL3.3_12X10NM",
                "ATL3.3_12X10CM",
                "ATL3.2_12X8N",
                "ATL3.2_12X10C",
                "ATL3.3_12X10CC",
                "ATL3.3_12X10NM/L1",
                "ATL3.3_10X12C UL",
                "ATL3.3_12X8N/H",
                "ATL3.3_10X12N FCC",
                "ATL3.3_10X12C FCC",
                "ATL3.3_10X12N",
                "ATL3.3_12X10NW",
                "ATL3.3_12X12NW",
                "ATL3.3_114X114N/H",
                "ATL3.3_12X8C/H",
                "ATL3.3_115X100N",
                "ATL3.3_114X114N",
                "ATL3.3_12X8N/L1"
            ])
        )
        filter_list = {m.strip() for m in FILTER_MATERIALS.split("\n") if m.strip()}

        if st.button("Verwerken"):
            # 6) Clean keys
            def clean_col(df, col):
                df[col] = (df[col]
                           .astype(str)
                           .str.replace(r'\.0$', '', regex=True)
                           .str.strip())
            clean_col(df_amlog,   amlog_ref)
            clean_col(df_export,  export_purch)
            clean_col(df_export,  export_project)
            clean_col(df_zstatus, zstatus_projref)

            # 7) Merge AM LOG ↔ EXPORT
            df12 = pd.merge(
                df_amlog,
                df_export,
                left_on=amlog_ref,
                right_on=export_purch,
                how="left",
                suffixes=("_amlog","_exp")
            )
            st.write(f"Na eerste merge: {len(df12)} rijen")

            # 8) Merge ↔ ZSTATUS
            df123 = pd.merge(
                df12,
                df_zstatus,
                left_on=export_project,
                right_on=zstatus_projref,
                how="left",
                suffixes=("","_zst")
            )
            st.write(f"Na tweede merge: {len(df123)} rijen")

            # 9) Filter op Material‐kolom van EXPORT
            if "Material" not in df123.columns:
                st.error("Kolom 'Material' niet gevonden in de merged data.")
                return
            df_filtered = df123[df123["Material"].astype(str).isin(filter_list)].copy()
            st.write(f"Na filter op Material: {len(df_filtered)} rijen")

            # 10) Toon en download
            cols_to_show = [amlog_ref, amlog_eq, amlog_sn, "Material", export_project]
            st.dataframe(df_filtered[cols_to_show].head(100))

            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df_filtered.to_excel(writer, index=False, sheet_name="Filtered")
            st.download_button(
                label="Download filtered merge",
                data=buf.getvalue(),
                file_name="filtered_merged_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Er ging iets mis: {e}")
else:
    st.info("Upload alle drie de bestanden om verder te gaan.")
