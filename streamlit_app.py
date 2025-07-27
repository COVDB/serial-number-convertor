<<<<<<< a7xfad-codex/find-and-fix-a-bug-in-codebase
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
EQUIPMENT_LIST = [e.zfill(18) for e in EQUIPMENT_LIST]
CHECK_EQUIP = '000000000010001878'
if CHECK_EQUIP in EQUIPMENT_LIST:
    st.sidebar.info(f"Test value {CHECK_EQUIP} found in equipment list")
else:
    st.sidebar.warning(f"Test value {CHECK_EQUIP} NOT found in equipment list")

def find_col(df, keyword_list):
    for kw in keyword_list:
        for col in df.columns:
            if kw.lower() in col.lower():
                return col
    return None

if st.sidebar.button("Run Merge"):
    if not (am_log_file and zsd_file and zstatus_file):
        st.error("Please upload all three files to proceed.")
        st.stop()

    # Load and clean
    am_df = pd.read_excel(am_log_file, dtype=str)
    am_df.columns = am_df.columns.str.strip()
    zsd_df = pd.read_excel(zsd_file, dtype=str)
    zsd_df.columns = zsd_df.columns.str.strip()
    zstatus_df = pd.read_excel(zstatus_file, dtype=str)
    zstatus_df.columns = zstatus_df.columns.str.strip()

    # Identify equipment column
    equip_col = find_col(am_df, ['equipment number', 'equipment'])
    if not equip_col:
        st.error("Kan kolom 'Equipment number' niet vinden in AM LOG.")
        st.write(am_df.columns.tolist())
        st.stop()

    # Clean equipment values to string of digits
    am_df[equip_col] = (
        am_df[equip_col]
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(18)
    )

    # Debug cleaned equipment values
    st.subheader("Equipment column cleaned & sample values")
    st.write(f"Column used: '{equip_col}' with dtype {am_df[equip_col].dtype}")
    st.write(am_df[equip_col].unique()[:10])
    common = set(am_df[equip_col].unique()).intersection(EQUIPMENT_LIST)
    st.write(f"Matches with EQUIPMENT_LIST: {len(common)} => {list(common)[:10]}")

    # Map other AM LOG cols
    cust_ref_col = find_col(am_df, ['customer reference', 'purch.doc', 'purch doc'])
    serial_col = find_col(am_df, ['serial'])
    desc_col = find_col(am_df, ['short text', 'description'])
    date_col = find_col(am_df, ['delivery date', 'date'])
    if not all([cust_ref_col, serial_col, desc_col, date_col]):
        st.error("Ontbrekende kolommen in AM LOG voor verdere verwerking.")
        st.stop()

    # Filter
    am_filtered = am_df[am_df[equip_col].isin(EQUIPMENT_LIST)].copy()
    st.subheader("Filtered AM LOG")
    st.write(am_filtered.shape)
    st.dataframe(am_filtered[[equip_col, cust_ref_col]].head())
    st.stop()

    # ----- Rest of processing disabled while debugging filter -----
    # Build temp
    temp = am_filtered[[cust_ref_col, serial_col, desc_col, date_col]].copy()
    temp.columns = ['Customer Reference', 'Serial number', 'Short text for sales order item', 'Delivery Date']
    temp['Delivery Date'] = pd.to_datetime(temp['Delivery Date'], errors='coerce')
    temp['Year of construction'] = temp['Delivery Date'].dt.year.astype('Int64')
    temp['Month of construction'] = temp['Delivery Date'].dt.strftime('%m')
    st.subheader("Temp after date parse")
    st.dataframe(temp.head())

    # Prepare ZSD
    zsd_cust = find_col(zsd_df, ['purch.doc', 'customer reference'])
    zsd_doc = find_col(zsd_df, ['document'])
    zsd_mat = find_col(zsd_df, ['material'])
    zsd_proj = find_col(zsd_df, ['project reference'])
    if not all([zsd_cust, zsd_doc, zsd_mat, zsd_proj]):
        st.error("Ontbrekende kolommen in ZSD_PO_PER_SO.")
        st.stop()
    zsd_df = zsd_df.rename(columns={
        zsd_cust: 'Customer Reference', zsd_doc: 'ZSD Document',
        zsd_mat: 'ZSD Material', zsd_proj: 'Project Reference'
    })[['Customer Reference','ZSD Document','ZSD Material','Project Reference']]
    st.subheader("ZSD sample")
    st.dataframe(zsd_df.head())

    merged1 = temp.merge(zsd_df, on='Customer Reference', how='inner')
    st.subheader("Merged1 (inner join)")
    st.write(merged1.shape)
    st.dataframe(merged1.head())

    # Prepare ZSTATUS
    zs_doc = find_col(zstatus_df, ['document'])
    zs_cols = {find_col(zstatus_df, [k.lower()]): k for k in ['Sold-to pt','Ship-to','CoSPa','Date OKWV']}
    if not zs_doc or any(col is None for col in zs_cols.keys()):
        st.error("Ontbrekende kolommen in ZSTATUS.")
        st.stop()
    zstatus_df = zstatus_df.rename(columns={zs_doc:'ZSD Document', **zs_cols})[['ZSD Document', *zs_cols.values()]]
    st.subheader("ZSTATUS sample")
    st.dataframe(zstatus_df.head())

    final_df = merged1.merge(zstatus_df, on='ZSD Document', how='left')
    st.subheader("Final merged")
    st.write(final_df.shape)
    st.dataframe(final_df.head())

    # Download
    buffer = BytesIO()
    final_df.to_excel(buffer, index=False, sheet_name='MergedData')
    buffer.seek(0)
    st.download_button("Download merged Excel", data=buffer,
        file_name="merged_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
=======
>>>>>>> main


