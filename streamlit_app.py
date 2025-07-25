import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Serial Number Merger", layout="centered")
st.title("Serial Number Merger")

st.write("""
1. Upload het **AM LOG EQUIPMENT LIST** bestand  
2. Upload het **Export** bestand  
3. Upload de **ZSTATUS** export file  
4. (Optioneel) Pas kolommen aan als nodig  
5. Filter op 'equipment group' indien gewenst  
6. Klik op 'Verwerken'
""")

# --- Materiaalgroepen bovenin ---
SHUTTLE_CODES = [ ... ]  # Plaats hier jouw volledige lijst (zoals je nu hebt)
BCC_CODES = [ ... ]      # idem
MCC_CODES = [ ... ]      # idem

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

        # --- Automatische kolomkoppeling (default op naam) ---
        auto_map_amlog = {
            "Customer Reference (AM LOG)": "Customer Reference",
            "Equipment Number (AM LOG)": "Equipment Number",
            "Serial Number (AM LOG)": "Serial Number",
            "Material Number (AM LOG)": "Material Number",
            "Year of construction (AM LOG)": "Year of construction",
            "Month of construction (AM LOG)": "Month of construction"
        }
        auto_map_export = {
            "Purch.Doc (EXPORT)": "Purch.Doc",
            "Project Reference (EXPORT)": "Project Reference",
            "Document (EXPORT)": "Document",
            "Material (EXPORT)": "Material",
            "Sold-to party (EXPORT)": "Sold-to party",
            "Description (EXPORT)": "Description"
        }
        auto_map_zstatus = {
            "ProjRef (ZSTATUS)": "ProjRef",
            "Sold-to pt (ZSTATUS)": "Sold-to pt",
            "Ship-to (ZSTATUS)": "Ship-to",
            "Created on (ZSTATUS)": "Created on"
        }

        st.subheader("Kolomtoewijzing")
        edit_columns = st.checkbox("Kolommen wijzigen", value=False)

        # --- Kolomselectie, standaard op naam, optioneel dropdown ---
        amlog_cols = df_amlog.columns.tolist()
        export_cols = df_export.columns.tolist()
        zstatus_cols = df_zstatus.columns.tolist()

        def select_or_auto(label, default, options):
            if edit_columns:
                return st.selectbox(label, options, index=options.index(default) if default in options else 0)
            else:
                return default if default in options else options[0]

        amlog_ref_col = select_or_auto("Customer Reference (AM LOG)", auto_map_amlog["Customer Reference (AM LOG)"], amlog_cols)
        amlog_eq_col = select_or_auto("Equipment Number (AM LOG)", auto_map_amlog["Equipment Number (AM LOG)"], amlog_cols)
        amlog_sn_col = select_or_auto("Serial Number (AM LOG)", auto_map_amlog["Serial Number (AM LOG)"], amlog_cols)
        amlog_mat_col = select_or_auto("Material Number (AM LOG)", auto_map_amlog["Material Number (AM LOG)"], amlog_cols)
        amlog_year_col = select_or_auto("Year of construction (AM LOG)", auto_map_amlog["Year of construction (AM LOG)"], amlog_cols)
        amlog_month_col = select_or_auto("Month of construction (AM LOG)", auto_map_amlog["Month of construction (AM LOG)"], amlog_cols)

        export_ref_col = select_or_auto("Purch.Doc (EXPORT)", auto_map_export["Purch.Doc (EXPORT)"], export_cols)
        export_proj_col = select_or_auto("Project Reference (EXPORT)", auto_map_export["Project Reference (EXPORT)"], export_cols)
        export_doc_col = select_or_auto("Document (EXPORT)", auto_map_export["Document (EXPORT)"], export_cols)
        export_mat_col = select_or_auto("Material (EXPORT)", auto_map_export["Material (EXPORT)"], export_cols)
        export_sold_col = select_or_auto("Sold-to party (EXPORT)", auto_map_export["Sold-to party (EXPORT)"], export_cols)
        export_desc_col = select_or_auto("Description (EXPORT)", auto_map_export["Description (EXPORT)"], export_cols)

        zstatus_projref_col = select_or_auto("ProjRef (ZSTATUS)", auto_map_zstatus["ProjRef (ZSTATUS)"], zstatus_cols)
        zstatus_sold_col = select_or_auto("Sold-to pt (ZSTATUS)", auto_map_zstatus["Sold-to pt (ZSTATUS)"], zstatus_cols)
        zstatus_ship_col = select_or_auto("Ship-to (ZSTATUS)", auto_map_zstatus["Ship-to (ZSTATUS)"], zstatus_cols)
        zstatus_created_col = select_or_auto("Created on (ZSTATUS)", auto_map_zstatus["Created on (ZSTATUS)"], zstatus_cols)

        # --- Categorisatie en filtering ---
        df_amlog["Equipment Category Group"] = df_amlog[amlog_mat_col].apply(categorize_material)
        category_options = ["ALLE"] + sorted(df_amlog["Equipment Category Group"].unique())
        selected_category = st.selectbox(
            "Filter op equipment groep (uit AM LOG 'Material Number')",
            category_options
        )
        if selected_category != "ALLE":
            df_amlog = df_amlog[df_amlog["Equipment Category Group"] == selected_category]

        # --- Toon filtering-resultaat (optioneel) ---
        # st.write("Aantal rijen na filtering:", len(df_amlog))
        # st.write("Unieke categorieën na filtering:", df_amlog['Equipment Category Group'].unique())

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
            sap_output["Equipment Number"] = ""  # altijd leeg
            if date_col_name:
                if not pd.api.types.is_datetime64_any_dtype(merged[date_col_name]):
                    merged[date_col_name] = pd.to_datetime(merged[date_col_name], errors="coerce")
                sap_output["Date valid from"] = merged[date_col_name].dt.strftime("%d.%m.%Y")
            else:
                sap_output["Date valid from"] = ""
            sap_output["Equipment category"] = "S"
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
