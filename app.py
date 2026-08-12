import streamlit as st
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import pandas as pd

# 1. Page Configuration
st.set_page_config(
    page_title="Garment Production & Inspection Dashboard",
    page_icon="🧵",
    layout="wide"
)

st.title("🧵 Live Garment Production & Inspection Dashboard")
st.caption("Real-time data synced directly with Google Sheets")

# 2. Google Sheets Connection
# Replace with your actual public Google Sheets link
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1KGZmiPoeY1UPe0NPGdz4w7QE4MOlLvQKa6w58giDkW4/edit?usp=drivesdk"

@st.cache_data(ttl=30)  # Re-fetches fresh data every 30 seconds
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=GSHEET_URL, header=2)
    
    # Ensure numeric columns are properly formatted
    df["Order QTY"] = pd.to_numeric(df["Order QTY"], errors="coerce").fillna(0)
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

# 3. Sidebar Filters (Dynamic Multi-Select)
st.sidebar.header("🔍 Filter Dashboard")

# Floor Filter
floors = df_raw["Floor Name"].dropna().unique().tolist()
selected_floors = st.sidebar.multiselect("Select Floor(s):", options=floors, default=floors)

# Inspector Filter
inspectors = df_raw["Inspector Name"].dropna().unique().tolist()
selected_inspectors = st.sidebar.multiselect("Select Inspector(s):", options=inspectors, default=inspectors)

# Inline vs Final Filter
inspection_types = df_raw["Inline/Final"].dropna().unique().tolist()
selected_types = st.sidebar.multiselect("Inspection Type:", options=inspection_types, default=inspection_types)

# Apply Filters
filtered_df = df_raw[
    (df_raw["Floor Name"].isin(selected_floors)) &
    (df_raw["Inspector Name"].isin(selected_inspectors)) &
    (df_raw["Inline/Final"].isin(selected_types))
]

# 4. Top KPI Summary Cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric("Total Order Quantity", f"{int(filtered_df['Order QTY'].sum()):,}")
with kpi2:
    st.metric("Total PO Count", f"{int(filtered_df['Total PO'].sum()):,}")
with kpi3:
    st.metric("Total Inspections", f"{len(filtered_df):,}")
with kpi4:
    unique_styles = filtered_df["Style Name"].nunique() if "Style Name" in filtered_df else 0
    st.metric("Active Styles", unique_styles)

st.divider()

# 5. Graphical Visualizations
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📊 Order Quantity by Floor")
    fig_floor = px.bar(
        filtered_df,
        x="Floor Name",
        y="Order QTY",
        color="Inline/Final",
        barmode="group",
        title="Order Qty Split by Floor & Inspection Type",
        text_auto=True
    )
    fig_floor.update_layout(xaxis_title="", yaxis_title="Quantity")
    st.plotly_chart(fig_floor, use_container_width=True)

with col_chart2:
    st.subheader("🎯 Inspection Type Distribution")
    fig_pie = px.pie(
        filtered_df,
        names="Inline/Final",
        values="Order QTY",
        hole=0.4,
        title="Inline vs. Final Inspection Ratio (by Order QTY)",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# 6. Detailed Data Table
st.subheader("📋 Raw Inspection Data")

# Style name search bar
search_style = st.text_input("🔎 Search by Style Name or PO Number:")
if search_style:
    filtered_df = filtered_df[
        filtered_df["Style Name"].astype(str).str.contains(search_style, case=False) |
        filtered_df["PO numbers"].astype(str).str.contains(search_style, case=False)
    ]

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)
