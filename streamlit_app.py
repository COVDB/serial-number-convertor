import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Serial Number Merger", layout="centered")
st.title("Serial Number Merger")

st.write("""
1. Upload het **AM LOG EQUIPMENT LIST** bestand  
2. Upload het **Export** bestand  
3. Upload de **ZSTATUS** export file  
4. Selecteer de juiste kolommen  
5. Filter op 'equipment group' indien gewenst  
6. Klik op 'Verwerken'
""")

# --- Zet je lijst met SHUTTLE, BCC, MCC codes bovenin het script ---
SHUTTLE_CODES = [
    "000000000001001917","000000000001001808","000000000001001749","000000000001001776",
    "000000000001001911","000000000001001755","000000000001001760","000000000001001809",
    "000000000001001792","000000000001001747","000000000001001711","000000000001001757",
    "000000000001001708","000000000001001850","000000000001001770","000000000001001852",
    "000000000001001710","000000000001001771","000000000001001758","000000000001001753",
    "000000000001001795","000000000001001845","000000000001001752","000000000001008374",
    "000000000001001805","000000000001001709","000000000001008560","000000000001001765",
    "000000000001001775","000000000001008561","000000000001009105","000000000001001777",
    "000000000001001742","000000000001001813","000000000001009719","000000000010005396",
    "000000000010003687","000000000010005397"
]

BCC_CODES = [
    "000000000001006284","000000000001006280","000000000001006288","000000000001006348",
    "000000000001007919","000000000001006352","000000000001006286","000000000001006346",
    "000000000001006278","000000000001007911","000000000001007927","000000000001007921",
    "000000000001007925","000000000001007923","000000000001007915","000000000001008578",
    "000000000001007928","000000000001007909","000000000001007913","000000000001007917"
]

MCC_CODES = [
    "000000000001006304","000000000001006271","000000000001006250","000000000001006294",
    "000000000001006241","000000000001006248","000000000001006293","000000000001006270",
    "000000000001008135","000000000001006201","000000000001006240","000000000001008131",
    "000000000001006269","000000000001006247","000000000001006273","000000000001008251",
    "000000000001008576","000000000001008253","000000000001009225","000000000001009454"
]

def categorize_material(mat_num):
    s = str(mat_num).zfill(18)
    if s in SHUTTLE_CODES:
        return "SHUTTLE"
    elif s in MCC_CODES:
        return "MCC"
    elif s in BCC_CODES:
        return "BCC"
    else:
        return "OTHER"

amlog_file = st.file_uploader("Upload AM LOG EQUIPMENT LIST", type=["xlsx"])
export_file = st.file_uploader("Upload Export bestand", type=["xlsx"])
zstatus_file = st.file_uploader("Upload ZSTATUS export", type=["xlsx"])

if amlog_file and export_file and zstatus_file:
    try:
        # Lees de bestanden in
        df_amlog = pd.read_excel(amlog_file)
        df_export = pd.read_excel(export_file)
        df_zstatus = pd.read_excel(zstatus_file)

        st.success("Alle bestanden ingelezen!")

        # --- Kolomselectie direct na upload ---
        amlog_cols = df_amlog.columns.tolist()
        amlog_mat_col = st.selectbox("Material Number (AM LOG)", amlog_cols)

        # --- Categorisatie en filtering ---
        df_amlog["Equipment Category Group"] = df_amlog[amlog_mat_col].apply(categorize_material)
        category_options = ["ALLE"] + sorted(df_amlog["Equipment Category Group"].unique())
        selected_category = st.selectbox(
            "Filter op equipment groep (uit AM LOG 'Material Number')",
            category_options
        )
        if selected_category != "ALLE":
            df_amlog = df_amlog[df_amlog["Equipment Category Group"] == selected_category]

        # Debug: Toon filtering-resultaat
        st.write("Aantal rijen na filtering:", len(df_amlog))
        st.write("Unieke categorieën na filtering:", df_amlog['Equipment Category Group'].unique())
        st.dataframe(df_amlog.head(20))

        # --- Overige kolomselecties ---
        st.write("**Stap 1: Selecteer de kolommen voor AM LOG**")
        amlog_ref_col = st.selectbox("Customer Reference (AM LOG)", amlog_cols)
        amlog_eq_col = st.selectbox("Equipment Number (AM LOG)", amlog_cols)
        amlog_sn_col = st.selectbox("Serial Number (AM LOG)", amlog_cols)
        amlog_year_col = st.selectbox("Year of construction (AM LOG)", amlog_cols)
        amlog_month_col = st.selectbox("Month of construction (AM LOG)", amlog_cols)

        # Stap 2: Kolomselectie EXPORT
        st.write("**Stap 2: Selecteer de kolommen voor EXPORT**")
        export_cols = df_export.columns.tolist()
        export_ref_col = st.selectbox("Purch.Doc (EXPORT)", export_cols)
        export_proj_col = st.selectbox("Project Reference (EXPORT)", export_cols)
        export_doc_col = st.selectbox("Document (EXPORT)", export_cols)
        export_mat_col = st.selectbox("Material (EXPORT)", export_cols)
        export_sold_col = st.selectbox("Sold-to party (EXPORT)", export_cols)
        export_desc_col = st.selectbox("Description (EXPORT)", export_cols)

        # Stap 3: Kolomselectie ZSTATUS
        st.write("**Stap 3: Selecteer de kolommen voor ZSTATUS**")
        zstatus_cols = df_zstatus.columns.tolist()
        zstatus_projref_col = st.selectbox("ProjRef (ZSTATUS)", zstatus_cols)
        zstatus_sold_col = st.selectbox("Sold-to pt (ZSTATUS)", zstatus_cols)
        zstatus_ship_col = st.selectbox("Ship-to (ZSTATUS)", zstatus_cols)
        zstatus_created_col = st.selectbox("Created on (ZSTATUS)", zstatus_cols)

        if st.button("Verwerken"):
            # --- CLEAN & SELECT ---
            amlog_sel = df_amlog[
                [amlog_ref_col, amlog_eq_col, amlog_sn_col, amlog_mat_col, "Equipment Category Group", amlog_year_col, amlog_month_col]
            ].copy()
            export_sel = df_export[
                [export_proj_col, export_doc_col, export_mat_col, export_sold_col, export_desc_col, export_ref_col]
            ].copy()
            zstatus_sel = df_zstatus[
                [zstatus_projref_col, zstatus_sold_col, zstatus_ship_col, zstatus_created_col]
            ].copy()

            # Clean merge keys
            def clean_reference(x):
                if pd.isnull(x):
                    return ""
                try:
                    return str(int(float(x))).strip()
                except:
                    return str(x).strip()

            amlog_sel[amlog_ref_col] = amlog_sel[amlog_ref_col].apply(clean_reference)
            export_sel[export_ref_col] = export_sel[export_ref_col].apply(clean_reference)
            zstatus_sel[zstatus_projref_col] = zstatus_sel[zstatus_projref_col].apply(clean_reference)

            # --- MERGE 1: AM LOG + EXPORT ---
            merged = pd.merge(
                amlog_sel,
                export_sel,
                left_on=amlog_ref_col,
                right_on=export_ref_col,
                how="left"
            )

            # --- MERGE 2: + ZSTATUS ---
            merged['Project Reference'] = merged[export_proj_col].astype(str).str.strip()
            zstatus_sel[zstatus_projref_col] = zstatus_sel[zstatus_projref_col].astype(str).str.strip()
            merged = pd.merge(
                merged,
                zstatus_sel,
                left_on='Project Reference',
                right_on=zstatus_projref_col,
                how='left',
                suffixes=('', '_zstatus')
            )

            # --- Zoek de correcte kolomnaam voor "Date valid from" ---
            merged_cols = merged.columns.tolist()
            date_col_name = zstatus_created_col
            if date_col_name not in merged_cols:
                candidates = [col for col in merged_cols if date_col_name in col]
                if candidates:
                    date_col_name = candidates[0]
                else:
                    st.error(f"Kolom '{zstatus_created_col}' niet gevonden in het samengevoegde bestand!")
                    date_col_name = None

            # --- SAP OUTPUT ---
            sap_output = pd.DataFrame()
            sap_output["Equipment Number"] = ""  # altijd leeg (of zet hier wat je wil uploaden)
            if date_col_name:
                if not pd.api.types.is_datetime64_any_dtype(merged[date_col_name]):
                    merged[date_col_name] = pd.to_datetime(merged[date_col_name], errors="coerce")
                sap_output["Date valid from"] = merged[date_col_name].dt.strftime("%d.%m.%Y")
            else:
                sap_output["Date valid from"] = ""
            sap_output["Equipment category"] = "S"  # zet hier 's' (zoals gewenst door SAP)
            sap_output["Description"] = merged[export_desc_col]
            sap_output["Sold to partner"] = merged[zstatus_sold_col]
            sap_output["Ship to partner"] = merged[zstatus_ship_col]
            sap_output["Material Number"] = merged[export_mat_col]
            sap_output["Serial number"] = merged[amlog_sn_col]
            sap_output["Begin Guarantee"] = ""
            sap_output["Warranty end date"] = ""
            sap_output["Indicator, Whether Technical Object Should Inherit Warranty"] = "x"
            sap_output["Indicator: Pass on Warranty"] = "x"
            sap_output["Construction year"] = merged[amlog_year_col]
            sap_output["Construction month"] = merged[amlog_month_col]

            st.success(f"SAP output met {len(sap_output)} rijen klaar voor download.")
            st.dataframe(sap_output.head(100))

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                sap_output.to_excel(writer, index=False, sheet_name="SAP Upload")
            st.download_button(
                label="Download SAP-upload Excel",
                data=output.getvalue(),
                file_name="sap_upload.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"Fout bij verwerken: {e}")

else:
    st.info("Upload alle drie de bestanden om verder te gaan.")
