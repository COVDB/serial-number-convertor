import streamlit as st
import pandas as pd
import io
import traceback

st.set_page_config(page_title="Serial Number Merger", layout="centered")
st.title("Serial Number Merger")

st.write("""
1. Upload het **AM LOG EQUIPMENT LIST** bestand  
2. Upload het **Export** bestand  
3. Upload de **ZSTATUS** export file  
4. (Optioneel) Pas kolommen aan indien nodig  
5. Filter op 'equipment group' indien gewenst  
6. Klik op 'Verwerken'
""")

# --- Materiaalgroepen bovenin ---
SHUTTLE_CODES = [ "000000000001001917", "000000000001001808", /*…*/ "000000000001009719" ]
BCC_CODES     = [ "000000000001006284", /*…*/ "000000000001007917" ]
MCC_CODES     = [ "000000000001006304", /*…*/ "000000000001009454" ]

def safe_material_number(x):
    try:
        if pd.isnull(x) or str(x).strip().lower() in ["", "null", "(null)"]:
            return ""
        return str(int(float(x))).zfill(18)
    except:
        return ""

def categorize_material(mat_num):
    if mat_num in SHUTTLE_CODES:
        return "SHUTTLE"
    elif mat_num in MCC_CODES:
        return "MCC"
    elif mat_num in BCC_CODES:
        return "BCC"
    else:
        return "OTHER"

amlog_file   = st.file_uploader("Upload AM LOG EQUIPMENT LIST", type=["xlsx"])
export_file  = st.file_uploader("Upload Export bestand",        type=["xlsx"])
zstatus_file = st.file_uploader("Upload ZSTATUS export",        type=["xlsx"])

if amlog_file and export_file and zstatus_file:
    try:
        # Lees in
        df_amlog   = pd.read_excel(amlog_file)
        df_export  = pd.read_excel(export_file)
        df_zstatus = pd.read_excel(zstatus_file)
        st.success("Alle bestanden ingelezen!")

        # Automatische kolomkoppeling
        auto_map_amlog = {
            "Customer Reference (AMLOG)": "Customer Reference",
            "Equipment Number (AMLOG)"   : "Equipment Number",
            "Serial Number (AMLOG)"      : "Serial Number",
            "Material Number (AMLOG)"    : "Material Number",
            "Year of construction"       : "Year of construction",
            "Month of construction"      : "Month of construction"
        }
        auto_map_export = {
            "Purch.Doc"          : "Purch.Doc",
            "Project Reference"  : "Project Reference",
            "Document"           : "Document",
            "Material"           : "Material",
            "Sold-to party"      : "Sold-to party",
            "Description"        : "Description"
        }
        auto_map_zstatus = {
            "ProjRef"     : "ProjRef",
            "Sold-to pt"  : "Sold-to pt",
            "Ship-to"     : "Ship-to",
            "Created on"  : "Created on"
        }

        st.subheader("Kolomtoewijzing")
        edit_columns = st.checkbox("Kolommen wijzigen", value=False)

        amlog_cols, export_cols, zstatus_cols = (
            df_amlog.columns.tolist(),
            df_export.columns.tolist(),
            df_zstatus.columns.tolist()
        )
        def select_or_auto(label, default, options):
            if edit_columns:
                return st.selectbox(label, options, index=options.index(default) if default in options else 0)
            return default if default in options else options[0]

        # AMLOG
        amlog_ref_col   = select_or_auto("Customer Reference (AM LOG)",   "Customer Reference",   amlog_cols)
        amlog_eq_col    = select_or_auto("Equipment Number (AM LOG)",      "Equipment Number",     amlog_cols)
        amlog_sn_col    = select_or_auto("Serial Number (AM LOG)",         "Serial Number",        amlog_cols)
        amlog_mat_col   = select_or_auto("Material Number (AM LOG)",       "Material Number",      amlog_cols)
        amlog_year_col  = select_or_auto("Year of construction (AM LOG)",  "Year of construction", amlog_cols)
        amlog_month_col = select_or_auto("Month of construction (AM LOG)", "Month of construction",amlog_cols)

        # EXPORT
        export_ref_col  = select_or_auto("Purch.Doc (EXPORT)",         "Purch.Doc",         export_cols)
        export_proj_col = select_or_auto("Project Reference (EXPORT)","Project Reference",export_cols)
        export_doc_col  = select_or_auto("Document (EXPORT)",         "Document",          export_cols)
        export_mat_col  = select_or_auto("Material (EXPORT)",         "Material",          export_cols)
        export_sold_col = select_or_auto("Sold-to party (EXPORT)",    "Sold-to party",     export_cols)
        export_desc_col = select_or_auto("Description (EXPORT)",      "Description",       export_cols)

        # ZSTATUS
        zstatus_projref_col = select_or_auto("ProjRef (ZSTATUS)",   "ProjRef",  zstatus_cols)
        zstatus_sold_col    = select_or_auto("Sold-to pt (ZSTATUS)","Sold-to pt",zstatus_cols)
        zstatus_ship_col    = select_or_auto("Ship-to (ZSTATUS)",   "Ship-to",  zstatus_cols)
        zstatus_created_col = select_or_auto("Created on (ZSTATUS)","Created on",zstatus_cols)

        # Format & categoriseer Material Number
        df_amlog[amlog_mat_col] = df_amlog[amlog_mat_col].apply(safe_material_number)
        df_amlog["Equipment Category Group"] = df_amlog[amlog_mat_col].apply(categorize_material)
        cats = ["ALLE"] + sorted(df_amlog["Equipment Category Group"].unique())
        sel_cat = st.selectbox("Filter op equipment groep", cats)
        if sel_cat != "ALLE":
            df_amlog = df_amlog[df_amlog["Equipment Category Group"]==sel_cat]

        if st.button("Verwerken"):
            # Maak subsets
            amlog_sel  = df_amlog[[amlog_ref_col,amlog_eq_col,amlog_sn_col,amlog_mat_col,
                                   "Equipment Category Group",amlog_year_col,amlog_month_col]].copy()
            export_sel = df_export[[export_proj_col,export_doc_col,export_mat_col,
                                   export_sold_col,export_desc_col,export_ref_col]].copy()
            zstatus_sel= df_zstatus[[zstatus_projref_col,zstatus_sold_col,
                                    zstatus_ship_col,zstatus_created_col]].copy()

            # Vectorized clean keys
            for df, col in [(amlog_sel,amlog_ref_col),(export_sel,export_ref_col),(zstatus_sel,zstatus_projref_col)]:
                df[col] = (
                    df[col]
                    .astype(str)
                    .replace(r'^(nan|None|\(Null\))$', '', regex=True)
                    .str.replace(r'\.0$', '', regex=True)
                    .str.strip()
                )

            # Merge 1
            merged = pd.merge(amlog_sel, export_sel,
                              left_on=amlog_ref_col, right_on=export_ref_col,
                              how="left")
            # Merge 2
            merged['Project Reference'] = merged[export_proj_col].astype(str).str.strip()
            zstatus_sel[zstatus_projref_col] = zstatus_sel[zstatus_projref_col].astype(str).str.strip()
            merged = pd.merge(merged, zstatus_sel,
                              left_on='Project Reference', right_on=zstatus_projref_col,
                              how="left", suffixes=('','_zstatus'))

            # Bepaal date column name
            cols = merged.columns.tolist()
            date_col_name = zstatus_created_col if zstatus_created_col in cols else next((c for c in cols if zstatus_created_col in c), None)

            # Bouw SAP output
            sap_output = pd.DataFrame()
            sap_output["Equipment Number"] = ""
            if isinstance(date_col_name,str) and date_col_name in merged:
                merged[date_col_name] = pd.to_datetime(merged[date_col_name], errors="coerce")
                sap_output["Date valid from"] = merged[date_col_name].dt.strftime("%d.%m.%Y")
            else:
                sap_output["Date valid from"] = ""
            sap_output["Equipment category"] = "S"
            sap_output["Description"]      = merged[export_desc_col]
            sap_output["Sold to partner"]  = merged[zstatus_sold_col]
            sap_output["Ship to partner"]  = merged[zstatus_ship_col]
            sap_output["Material Number"]  = merged[export_mat_col]
            sap_output["Serial number"]    = merged[amlog_sn_col]
            sap_output["Begin Guarantee"]  = ""
            sap_output["Warranty end date"]= ""
            sap_output["Indicator, Whether Technical Object Should Inherit Warranty"] = "x"
            sap_output["Indicator: Pass on Warranty"] = "x"
            sap_output["Construction year"]  = merged[amlog_year_col]
            sap_output["Construction month"] = merged[amlog_month_col]

            st.success(f"SAP output met {len(sap_output)} rijen klaar voor download.")
            st.dataframe(sap_output.head(100))

            # Download
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                sap_output.to_excel(writer, index=False, sheet_name="SAP Upload")
            st.download_button("Download SAP-upload Excel", buf.getvalue(),
                               file_name="sap_upload.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        st.error(f"Fout bij verwerken: {e}")
        st.text(traceback.format_exc())

else:
    st.info("Upload alle drie de bestanden om verder te gaan.")
