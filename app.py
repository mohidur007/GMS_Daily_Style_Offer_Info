import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Configuration
st.set_page_config(
    page_title="GMS COMPOSITE Daily Style Offer Information",
    page_icon="🧵",
    layout="wide"
)

# Custom Gradient Title Styling
st.markdown("""
    <style>
    .gradient-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #4285F4, #9B51E0, #D946EF, #FF4B4B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        padding-bottom: 5px;
    }
    </style>
    <h1 class="gradient-title">GMS COMPOSITE Daily Style Offer Information</h1>
""", unsafe_allow_html=True)

st.caption("Real-time data synced directly with Register Khata")

# 2. Google Sheets Connection
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1KGZmiPoeY1UPe0NPGdz4w7QE4MOlLvQKa6w58giDkW4/edit?usp=drivesdk"

@st.cache_data(ttl=30)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=GSHEET_URL, header=2)
    
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    
    # Ensure numeric columns are properly formatted
    if "Order QTY" in df.columns:
        df["Order QTY"] = pd.to_numeric(df["Order QTY"], errors="coerce").fillna(0)
    if "Total PO" in df.columns:
        df["Total PO"] = pd.to_numeric(df["Total PO"], errors="coerce").fillna(0)
    
    # Format Date
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
        
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Error loading Google Sheet data: {e}")
    st.stop()

# 3. Sidebar Filters
st.sidebar.header("🔍 Filter Dashboard")

def get_column_data(df, col_name):
    return df[col_name].dropna().unique().tolist() if col_name in df.columns else []

floors = get_column_data(df_raw, "Floor Name")
selected_floors = st.sidebar.multiselect("Select Floor(s):", options=floors, default=floors)

inspectors = get_column_data(df_raw, "Inspector Name")
selected_inspectors = st.sidebar.multiselect("Select Inspector(s):", options=inspectors, default=inspectors)

inspection_types = get_column_data(df_raw, "Inline/Final")
selected_types = st.sidebar.multiselect("Inspection Type:", options=inspection_types, default=inspection_types)

# Filter dataframe safely
filtered_df = df_raw.copy()
if "Floor Name" in filtered_df.columns and selected_floors:
    filtered_df = filtered_df[filtered_df["Floor Name"].isin(selected_floors)]
if "Inspector Name" in filtered_df.columns and selected_inspectors:
    filtered_df = filtered_df[filtered_df["Inspector Name"].isin(selected_inspectors)]
if "Inline/Final" in filtered_df.columns and selected_types:
    filtered_df = filtered_df[filtered_df["Inline/Final"].isin(selected_types)]

# 4. Top KPI Summary Cards
col1, col2, col3 = st.columns(3)

total_styles = filtered_df["Style Name"].nunique() if "Style Name" in filtered_df.columns else 0
total_po = int(filtered_df['Total PO'].sum()) if "Total PO" in filtered_df.columns else 0

# Count unique styles that have a non-empty Inspector Name (Inspection Running)
if "Style Name" in filtered_df.columns and "Inspector Name" in filtered_df.columns:
    active_mask = filtered_df["Inspector Name"].notna() & (filtered_df["Inspector Name"].astype(str).str.strip() != "")
    active_styles = filtered_df[active_mask]["Style Name"].nunique()
else:
    active_styles = 0

# Custom CSS for Professional Button Style
st.markdown("""
    <style>
    .kpi-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        border-color: #0d6efd;
    }
    .kpi-title {
        font-size: 13px;
        font-weight: 600;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 700;
        color: #1e293b;
    }
    </style>
""", unsafe_allow_html=True)

with col1:
    st.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-title">Total Style</div>
            <div class="kpi-value">{total_styles:,}</div>
        </div>
    ''', unsafe_allow_html=True)

with col2:
    st.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-title">Total PO</div>
            <div class="kpi-value">{total_po:,}</div>
        </div>
    ''', unsafe_allow_html=True)

with col3:
    st.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-title">Active Styles</div>
            <div class="kpi-value">{active_styles:,}</div>
        </div>
    ''', unsafe_allow_html=True)


import io

# 5. Detailed Data Table
st.subheader("📋 Raw Inspection Data")

# Search bar
search_style = st.text_input("🔎 Search by Style Name or PO Number:")
if search_style and not filtered_df.empty:
    style_mask = filtered_df["Style Name"].astype(str).str.contains(search_style, case=False) if "Style Name" in filtered_df.columns else False
    po_mask = filtered_df["PO Number"].astype(str).str.contains(search_style, case=False) if "PO Number" in filtered_df.columns else False
    filtered_df = filtered_df[style_mask | po_mask]

# Helper function to convert dataframe to Excel format
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inspection_Data')
    return output.getvalue()

# Excel Download Button
excel_data = convert_df_to_excel(filtered_df)

st.download_button(
    label="📊 Download as Excel (.xlsx)",
    data=excel_data,
    file_name="Inspection_Data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Display Table
st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)

