import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Excel Merge Tool", layout="wide")
st.title("Excel Merge & Filter App")

# Sidebar file upload
am_log_file = st.sidebar.file_uploader("Upload AM LOG file", type=["xlsx", "xls"], key="am_log")
zsd_file = st.sidebar.file_uploader("Upload ZSD_PO_PER_SO file", type=["xlsx", "xls"], key="zsd")
zstatus_file = st.sidebar.file_uploader("Upload ZSTATUS file", type=["xlsx", "xls"], key="zstatus")

# Equipment number filter list
EQUIPMENT_LIST = [
    '000000000001001917','000000000001001808','000000000001001749',
    '000000000001001776','000000000001001911','000000000001001755',
    '000000000001001760','000000000001001809','000000000001001747',
    '000000000001001711','000000000001001757','000000000001001708',
    '000000000001001770','000000000001001710','000000000001001771',
    '000000000001001758','000000000001007905','000000000001001753',
    '000000000001001752','000000000001008374','000000000001001805',
    '000000000001001709','000000000001008561','000000000001008560',
    '000000000001001765','000000000001001775','000000000001009105',
    '000000000001001777','000000000001001742','000000000001001813',
    '000000000001009719'
]

def find_col(df, keyword_list):
    for kw in keyword_list:
        for col in df.columns:
            if kw.lower() in col.lower():
                return col
    return None

if st.sidebar.button("Run Merge"):
    if not (am_log_file and zsd_file and zstatus_file):
        st.error("Please upload all three files to proceed.")
    else:
        # Read files and strip column names
        am_df = pd.read_excel(am_log_file, dtype=str)
        am_df.columns = am_df.columns.str.strip()
        zsd_df = pd.read_excel(zsd_file, dtype=str)
        zsd_df.columns = zsd_df.columns.str.strip()
        zstatus_df = pd.read_excel(zstatus_file, dtype=str)
        zstatus_df.columns = zstatus_df.columns.str.strip()

        # Dynamic column mapping for AM LOG
        equip_col = find_col(am_df, ['equipment'])
        cust_ref_col = find_col(am_df, ['customer reference', 'purch.doc', 'purch doc'])
        serial_col = find_col(am_df, ['serial'])
        desc_col = find_col(am_df, ['short text', 'description'])
        date_col = find_col(am_df, ['delivery date', 'date'])
        if not all([equip_col, cust_ref_col, serial_col, desc_col, date_col]):
            st.error("Kan niet alle vereiste kolommen in AM LOG vinden. Controleer headers.")
            st.write(am_df.columns.tolist())
            st.stop()

        # Filter AM LOG
        am_filtered = am_df[am_df[equip_col].isin(EQUIPMENT_LIST)].copy()
        st.write(f"AM LOG gefilterd: {len(am_filtered)} rijen")

        # Create temp output
        temp = am_filtered[[cust_ref_col, serial_col, desc_col, date_col]].copy()
        temp = temp.rename(columns={
            cust_ref_col: 'Customer Reference',
            serial_col: 'Serial number',
            desc_col: 'Short text for sales order item',
            date_col: 'Delivery Date'
        })

        # Extract Year/Month
        temp['Delivery Date'] = pd.to_datetime(temp['Delivery Date'], errors='coerce')
        temp['Year of construction'] = temp['Delivery Date'].dt.year.astype('Int64')
        temp['Month of construction'] = temp['Delivery Date'].dt.strftime('%m')

        # Dynamic mapping for ZSD
        zsd_cust = find_col(zsd_df, ['purch.doc', 'customer reference'])
        zsd_doc = find_col(zsd_df, ['document'])
        zsd_mat = find_col(zsd_df, ['material'])
        zsd_proj = find_col(zsd_df, ['project reference'])
        if not all([zsd_cust, zsd_doc, zsd_mat, zsd_proj]):
            st.error("Kan niet alle vereiste kolommen in ZSD_PO_PER_SO vinden. Controleer headers.")
            st.write(zsd_df.columns.tolist())
            st.stop()

        zsd_df = zsd_df.rename(columns={
            zsd_cust: 'Customer Reference',
            zsd_doc: 'ZSD Document',
            zsd_mat: 'ZSD Material',
            zsd_proj: 'Project Reference'
        })
        zsd_df = zsd_df[['Customer Reference', 'ZSD Document', 'ZSD Material', 'Project Reference']]

        merged1 = temp.merge(zsd_df, on='Customer Reference', how='left')
        st.write(f"Na merge ZSD: {len(merged1)} rijen, mpackage matches: {merged1['ZSD Document'].notna().sum()} ")

        # Dynamic mapping for ZSTATUS
        zs_doc = find_col(zstatus_df, ['document'])
        zs_cols = { 
            'Sold-to pt': find_col(zstatus_df, ['sold-to']),
            'Ship-to': find_col(zstatus_df, ['ship-to']),
            'CoSPa': find_col(zstatus_df, ['cospa']),
            'Date OKWV': find_col(zstatus_df, ['date okwv'])
        }
        if not zs_doc or any(v is None for v in zs_cols.values()):
            st.error("Kan niet alle vereiste kolommen in ZSTATUS vinden. Controleer headers.")
            st.write(zstatus_df.columns.tolist())
            st.stop()

        zstatus_df = zstatus_df.rename(columns={zs_doc: 'ZSD Document', **zs_cols})
        final_df = merged1.merge(
            zstatus_df[['ZSD Document', *zs_cols.keys()]],
            on='ZSD Document', how='left'
        )

        st.success("Merge complete!")
        st.dataframe(final_df)
        buffer = BytesIO()
        final_df.to_excel(buffer, index=False, sheet_name='MergedData')
        buffer.seek(0)
        st.download_button(
            label="Download merged Excel",
            data=buffer,
            file_name="merged_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
