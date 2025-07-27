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

def check_columns(df, expected, df_name):
    missing = [col for col in expected if col not in df.columns]
    if missing:
        st.error(
            f"Fout: In {df_name} ontbreken de kolommen: {', '.join(missing)}"
        )
        st.write(f"Beschikbare kolommen in {df_name}:")
        st.dataframe(pd.DataFrame({'Columns': df.columns}))
        return False
    return True

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

        # Validate AM LOG columns
        am_expected = ['Equipment number', 'Customer Reference', 'Serial number',
                       'Short text for sales order item', 'Delivery Date']
        if not check_columns(am_df, am_expected, 'AM LOG'):
            st.stop()

        # Step 1: Filter AM LOG
        am_filtered = am_df[am_df['Equipment number'].isin(EQUIPMENT_LIST)].copy()

        # Step 2: Create temp output from AM LOG
        temp = am_filtered[[
            'Customer Reference', 'Serial number',
            'Short text for sales order item', 'Delivery Date'
        ]].copy()

        # Extract Year and Month
        temp['Delivery Date'] = pd.to_datetime(temp['Delivery Date'], errors='coerce')
        temp['Year of construction'] = temp['Delivery Date'].dt.year.astype('Int64')
        temp['Month of construction'] = temp['Delivery Date'].dt.strftime('%m')

        # Validate ZSD_PO_PER_SO columns
        zsd_expected = ['Purch.Doc.', 'Document', 'Material', 'Project Reference']
        if not check_columns(zsd_df, zsd_expected, 'ZSD_PO_PER_SO'):
            st.stop()

        # Prepare ZSD: rename and select
        zsd_df = zsd_df.rename(columns={
            'Purch.Doc.': 'Customer Reference',
            'Document': 'ZSD Document',
            'Material': 'ZSD Material'
        })
        zsd_df = zsd_df[['Customer Reference', 'ZSD Document', 'ZSD Material', 'Project Reference']]

        # Step 3: Merge with ZSD_PO_PER_SO
        merged1 = temp.merge(
            zsd_df,
            on='Customer Reference', how='left'
        )

        # Validate ZSTATUS columns
        zstatus_expected = ['Document', 'Sold-to pt', 'Ship-to', 'CoSPa', 'Date OKWV']
        if not check_columns(zstatus_df, zstatus_expected, 'ZSTATUS'):
            st.stop()

        # Prepare ZSTATUS
        zstatus_df = zstatus_df.rename(columns={'Document': 'ZSD Document'})

        # Step 4: Merge with ZSTATUS
        final_df = merged1.merge(
            zstatus_df[['ZSD Document', 'Sold-to pt', 'Ship-to', 'CoSPa', 'Date OKWV']],
            on='ZSD Document', how='left'
        )

        # Display and download
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
