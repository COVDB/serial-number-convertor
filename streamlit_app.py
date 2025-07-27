import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Serial Number Merger", layout="centered")
st.title("Serial Number Merger")

st.write("""
1. Upload het **AM LOG EQUIPMENT LIST** bestand  
2. Upload het **Export** bestand  
3. Upload de **ZSTATUS** export file  
4. Klik op 'Verwerken'
""")

# Uploaders
amlog_file   = st.file_uploader("1) AM LOG EQUIPMENT LIST (.xlsx)", type="xlsx")
export_file  = st.file_uploader("2) Export bestand (.xlsx)",         type="xlsx")
zstatus_file = st.file_uploader("3) ZSTATUS export (.xlsx)",         type="xlsx")

# De lijst met material numbers om te behouden
FILTER_MATERIALS = {
    "000000000001001917","000000000001001808","000000000001001749",
    "000000000001001776","000000000001001911","000000000001001755",
    "000000000001001760","000000000001001809","000000000001001747",
    "000000000001001711","000000000001001757","000000000001001708",
    "000000000001001770","000000000001001710","000000000001001771",
    "000000000001001758","000000000001007905","000000000001001753",
    "000000000001001752","000000000001008374","000000000001001805",
    "000000000001001709","000000000001008561","000000000001008560",
    "000000000001001765","000000000001001775","000000000001009105",
    "000000000001001777","000000000001001742","000000000001001813",
    "000000000001009719"
}

if amlog_file and export_file and zstatus_file:
    try:
        # 1) Inlezen
        df_amlog   = pd.read_excel(amlog_file)
        df_export  = pd.read_excel(export_file)
        df_zstatus = pd.read_excel(zstatus_file)
        
        # 2) Filter AM LOG op Material Number
        # Zorg dat je kolomnaam EXACT overeenkomt met je file
        mat_col = "Material Number"
        if mat_col not in df_amlog.columns:
            st.error(f"Kolom '{mat_col}' niet gevonden in AM LOG.")
        else:
            df_amlog_filtered = df_amlog[
                df_amlog[mat_col].astype(str).isin(FILTER_MATERIALS)
            ].copy()
            st.write(f"AM LOG gefilterd: van {len(df_amlog)} naar {len(df_amlog_filtered)} rijen.")

            # 3) Eerste merge: Customer Reference → Purch.Doc
            left_key  = "Customer Reference"
            right_key = "Purch.Doc"
            df12 = pd.merge(
                df_amlog_filtered,
                df_export,
                left_on=left_key,
                right_on=right_key,
                how="left",
                suffixes=("_amlog","_exp")
            )
            st.write("Na eerste merge (AMLOG ↔ Export):", len(df12), "rijen.")

            # 4) Tweede merge: Project Reference → ProjRef
            left_key2  = "Project Reference"
            right_key2 = "ProjRef"
            df123 = pd.merge(
                df12,
                df_zstatus,
                left_on=left_key2,
                right_on=right_key2,
                how="left",
                suffixes=("","_zst")
            )
            st.write("Na tweede merge (↔ ZSTATUS):", len(df123), "rijen.")

            # 5) Toon de eerste 100 rijen
            st.dataframe(df123.head(100))

            # 6) Download-button
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df123.to_excel(writer, index=False, sheet_name="Merged")
            st.download_button(
                "Download volledige merged Excel",
                data=buf.getvalue(),
                file_name="merged_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Fout bij verwerken: {e}")
        st.text(str(e))
else:
    st.info("Upload alle drie de bestanden om verder te gaan.")
