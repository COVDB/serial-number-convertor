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
5. Klik op 'Verwerken'
""")

# 1) Upload de bestanden
amlog_file   = st.file_uploader("1) AM LOG EQUIPMENT LIST (.xlsx)",   type="xlsx")
export_file  = st.file_uploader("2) Export bestand (.xlsx)",           type="xlsx")
zstatus_file = st.file_uploader("3) ZSTATUS export (.xlsx)",           type="xlsx")

if amlog_file and export_file and zstatus_file:
    try:
        # 2) Inlezen
        df_amlog   = pd.read_excel(amlog_file)
        df_export  = pd.read_excel(export_file)
        df_zstatus = pd.read_excel(zstatus_file)

        st.success("Bestanden ingelezen!")

        # 3) Kolomselectie voor de keys
        st.subheader("Selecteer de key-kolommen")

        amlog_col        = st.selectbox(
            "AM LOG: Customer Reference",
            df_amlog.columns,
            index=df_amlog.columns.get_loc("Customer Reference") if "Customer Reference" in df_amlog.columns else 0
        )
        amlog_mat_col    = st.selectbox(
            "AM LOG: Material Number",
            df_amlog.columns,
            index=df_amlog.columns.get_loc("Material Number")    if "Material Number"    in df_amlog.columns else 0
        )

        export_purch     = st.selectbox(
            "EXPORT: Purch.Doc",
            df_export.columns,
            index=df_export.columns.get_loc("Purch.Doc")            if "Purch.Doc"            in df_export.columns else 0
        )
        export_project   = st.selectbox(
            "EXPORT: Project Reference",
            df_export.columns,
            index=df_export.columns.get_loc("Project Reference")    if "Project Reference"    in df_export.columns else 0
        )

        zstatus_projref  = st.selectbox(
            "ZSTATUS: ProjRef",
            df_zstatus.columns,
            index=df_zstatus.columns.get_loc("ProjRef")           if "ProjRef"           in df_zstatus.columns else 0
        )

        # 4) Filterlijst voor material numbers
        FILTER_MATERIALS = {
            "000000000001001917","000000000001001808","000000000001001749","000000000001001776",
            "000000000001001911","000000000001001755","000000000001001760","000000000001001809",
            "000000000001001747","000000000001001711","000000000001001757","000000000001001708",
            "000000000001001770","000000000001001710","000000000001001771","000000000001001758",
            "000000000001007905","000000000001001753","000000000001001752","000000000001008374",
            "000000000001001805","000000000001001709","000000000001008561","000000000001008560",
            "000000000001001765","000000000001001775","000000000001009105","000000000001001777",
            "000000000001001742","000000000001001813","000000000001009719"
        }

        if st.button("Verwerken"):
            # 5) Filter AM LOG
            df_amlog_f = df_amlog[df_amlog[amlog_mat_col].astype(str).isin(FILTER_MATERIALS)].copy()
            st.write(f"AM LOG gefilterd: {len(df_amlog)} → {len(df_amlog_f)} rijen")

            # 6) Eerste merge: Customer Reference → Purch.Doc
            df12 = pd.merge(
                df_amlog_f,
                df_export,
                left_on=amlog_col,
                right_on=export_purch,
                how="left",
                su
