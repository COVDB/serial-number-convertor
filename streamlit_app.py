import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Excel Merge Tool", layout="wide")
st.title("Excel Merge & Filter App")

# Sidebar file upload
am_log_file = st.sidebar.file_uploader("Upload AM LOG file", type=["xlsx", "xls"], key="am_log")
zsd_file = st.sidebar.file_uploader("Upload ZSD_PO_PER_SO file", type=["xlsx", "xls"], key="zsd")
zstatus_file = st.sidebar.file_uploader("Upload ZSTATUS file", type=["xlsx", "xls"], key="zstatus")

# Material number filter list
MATERIAL_LIST = [
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
MATERIAL_LIST = [m.zfill(18) for m in MATERIAL_LIST]

CHECK_MATERIAL = '00000000001001917'
if CHECK_MATERIAL in MATERIAL_LIST:
    st.sidebar.info(f"Test value {CHECK_MATERIAL} found in material list")
else:
    st.sidebar.warning(f"Test value {CHECK_MATERIAL} NOT found in material list")

# Utility to find column by keyword
def find_col(df, keyword_list):
    for kw in keyword_list:
        for col in df.columns:
            if kw.lower() == col.lower() or kw.lower() in col.lower():
                return col
    return None

if st.sidebar.button("Run Merge"):
    # Validate file uploads
    if not (am_log_file and zsd_file and zstatus_file):
        st.error("Please upload all three files to proceed.")
        st.stop()

    # Load dataframes and strip headers
    am_df = pd.read_excel(am_log_file, dtype=str)
    am_df.columns = am_df.columns.str.strip()
    zsd_df = pd.read_excel(zsd_file, dtype=str)
    zsd_df.columns = zsd_df.columns.str.strip()
    zstatus_df = pd.read_excel(zstatus_file, dtype=str)
    zstatus_df.columns = zstatus_df.columns.str.strip()

    # Identify and clean Material Number column in AM LOG
    material_col = find_col(am_df, ['material number']) or find_col(am_df, ['material'])
    if not material_col:
        st.error("Kan kolom 'Material Number' niet vinden in AM LOG.")
        st.write(am_df.columns.tolist())
        st.stop()
    am_df[material_col] = (
        am_df[material_col].astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(18)
    )

    # Debug: show cleaned material sample
    st.subheader("Material Number cleaned & matches")
    st.write(f"Column used: {material_col}")
    common = set(am_df[material_col].unique()).intersection(MATERIAL_LIST)
    st.write(f"Matches: {len(common)} -> {list(common)[:10]}")

    # Map other AM LOG columns, prioritizing exact matches
    cust_ref_col = find_col(am_df, ['customer reference', 'purch.doc'])
    serial_col = find_col(am_df, ['serial number']) or find_col(am_df, ['serial'])
    desc_col = find_col(am_df, ['short text']) or find_col(am_df, ['description'])
    date_col = find_col(am_df, ['delivery date']) or find_col(am_df, ['date'])
    if not all([cust_ref_col, serial_col, desc_col, date_col]):
        st.error("Ontbrekende kolommen in AM LOG voor verdere verwerking.")
        st.write(am_df.columns.tolist())
        st.stop()

    # Filter AM LOG on Material Number
    am_filtered = am_df[am_df[material_col].isin(MATERIAL_LIST)].copy()
    st.subheader("Filtered AM LOG by Material Number")
    st.write(f"Rows: {am_filtered.shape[0]}")
    st.dataframe(am_filtered[[material_col, cust_ref_col]].head())

    # Build temporary table
    temp = am_filtered[[cust_ref_col, serial_col, desc_col, date_col]].copy()
    temp.columns = ['Customer Reference', 'Serial number', 'Short text for sales order item', 'Delivery Date']
    temp['Delivery Date'] = pd.to_datetime(temp['Delivery Date'], errors='coerce')
    temp['Year of construction'] = temp['Delivery Date'].dt.year.astype('Int64')
    temp['Month of construction'] = temp['Delivery Date'].dt.strftime('%m')
    st.subheader("Temporary Table")
    st.dataframe(temp.head())

    # Prepare ZSD_PO_PER_SO merge
    zsd_cust = find_col(zsd_df, ['purch.doc', 'customer reference'])
    zsd_doc = find_col(zsd_df, ['document'])
    zsd_mat = find_col(zsd_df, ['material'])
    zsd_proj = find_col(zsd_df, ['project reference'])
    if not all([zsd_cust, zsd_doc, zsd_mat, zsd_proj]):
        st.error("Ontbrekende kolommen in ZSD_PO_PER_SO.")
        st.write(zsd_df.columns.tolist())
        st.stop()
    zsd_df = zsd_df.rename(columns={
        zsd_cust: 'Customer Reference',
        zsd_doc: 'ZSD Document',
        zsd_mat: 'ZSD Material',
        zsd_proj: 'Project Reference'
    })[['Customer Reference','ZSD Document','ZSD Material','Project Reference']]
    merged1 = temp.merge(zsd_df, on='Customer Reference', how='left')
    st.subheader("Merge with ZSD_PO_PER_SO")
    st.write(f"Rows: {merged1.shape[0]}, Matches: {merged1['ZSD Document'].notna().sum()}")
    st.dataframe(merged1.head())

    # Prepare ZSTATUS merge
    zs_doc = find_col(zstatus_df, ['document'])
    zs_cols = {
        'Sold-to pt': find_col(zstatus_df, ['sold-to pt']) or find_col(zstatus_df, ['sold-to']),
        'Ship-to': find_col(zstatus_df, ['ship-to']),
        'CoSPa': find_col(zstatus_df, ['cospa']),
        'Date OKWV': find_col(zstatus_df, ['date okwv'])
    }
    if not zs_doc or any(v is None for v in zs_cols.values()):
        st.error("Ontbrekende kolommen in ZSTATUS.")
        st.write(zstatus_df.columns.tolist())
        st.stop()
    zstatus_df = zstatus_df.rename(columns={zs_doc: 'ZSD Document', **zs_cols})[['ZSD Document', *zs_cols.keys()]]
    final_df = merged1.merge(zstatus_df, on='ZSD Document', how='left')
    st.subheader("Final Merged DataFrame")
    st.write(f"Rows: {final_df.shape[0]}")
    st.dataframe(final_df.head())

    # Download result
    buffer = BytesIO()
    final_df.to_excel(buffer, index=False, sheet_name='MergedData')
    buffer.seek(0)
    st.download_button(
        label="Download merged Excel",
        data=buffer,
        file_name="merged_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
