"""GreenFix Solutions interactive business dashboard.

Run with: streamlit run app.py
Dependencies: streamlit, pandas, plotly, requests
"""

from __future__ import annotations

from datetime import date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="GreenFix Solutions Analytics",
    page_icon="🌿",
    layout="wide"
)

# Google Sheet Details
SHEET_ID = "1xykvN_cVO5GXbiUtuP4yyj6dSjYpdu14vePaqhqYgVQ"
GID = "591451057"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

TIME_ORDER = ["Morning", "Afternoon", "Evening", "Night"]
CLIENT_ORDER = ["Loyal", "Returning", "New"]

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    df["Date"] = pd.to_datetime(df["Date"])
    # Calculate ROAS and CPA per row
    df["ROAS"] = df["Revenue"] / df["Ad Spend"].replace(0, pd.NA)
    df["CPA"] = df["Ad Spend"] / df["Conversions"].replace(0, pd.NA)
    return df

try:
    raw_df = load_data()
except Exception as e:
    st.error(f"Error loading data from Google Sheets: {e}")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.title("🔍 Filters")

min_date = raw_df["Date"].min().date()
max_date = raw_df["Date"].max().date()

picked_dates = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(picked_dates, (tuple, list)) and len(picked_dates) == 2:
    start_date, end_date = picked_dates
else:
    start_date = end_date = picked_dates[0] if picked_dates else min_date

client_options = sorted(raw_df["Client Type"].dropna().unique().tolist())
selected_clients = st.sidebar.multiselect("Client Type", client_options, default=client_options)

service_options = sorted(raw_df["Service Category"].dropna().unique().tolist())
selected_services = st.sidebar.multiselect("Service Category", service_options, default=service_options)

# Filter Data
filtered_df = raw_df[
    (raw_df["Date"].dt.date >= start_date) &
    (raw_df["Date"].dt.date <= end_date) &
    (raw_df["Client Type"].isin(selected_clients)) &
    (raw_df["Service Category"].isin(selected_services))
].copy()

# --- Title & Header Metrics ---
st.title("🌿 GreenFix Solutions - Business Performance Dashboard")
st.markdown("Interactive analytics dashboard for performance, customer LTV, and seasonal service optimization in Abu Dhabi.")

st.divider()

total_revenue = filtered_df["Revenue"].sum()
total_ad_spend = filtered_df["Ad Spend"].sum()
total_conversions = filtered_df["Conversions"].sum()

overall_roas = total_revenue / total_ad_spend if total_ad_spend > 0 else 0
overall_cpa = total_ad_spend / total_conversions if total_conversions > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${total_revenue:,.2f}")
col2.metric("Total Ad Spend", f"${total_ad_spend:,.2f}")
col3.metric("Overall ROAS", f"{overall_roas:.2f}x")
col4.metric("Overall CPA", f"${overall_cpa:.2f}")

st.divider()

# --- Dashboard Tabs ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 Growth & Services", 
    "👥 Customer LTV", 
    "⏰ Timing & Seasonality", 
    "💡 Actionable Recommendations"
])

# Tab 1: Growth & Services
with tab1:
    st.subheader("Service Category Performance & Growth Areas")
    
    service_summary = filtered_df.groupby("Service Category").agg(
        Total_Revenue=("Revenue", "sum"),
        Total_Ad_Spend=("Ad Spend", "sum"),
        Total_Conversions=("Conversions", "sum")
    ).reset_index()
    
    service_summary["ROAS"] = service_summary["Total_Revenue"] / service_summary["Total_Ad_Spend"]
    service_summary = service_summary.sort_values(by="Total_Revenue", ascending=False)
    
    fig_service = px.bar(
        service_summary,
        x="Service Category",
        y=["Total_Revenue", "Total_Ad_Spend"],
        barmode="group",
        title="Revenue vs. Ad Spend by Service Category",
        labels={"value": "Amount ($)", "variable": "Metric"},
        color_discrete_sequence=["#2ea043", "#f85149"]
    )
    st.plotly_chart(fig_service, use_container_width=True)
    
    st.dataframe(service_summary.style.format({
        "Total_Revenue": "${:,.2f}",
        "Total_Ad_Spend": "${:,.2f}",
        "ROAS": "{:.2f}x"
    }), use_container_width=True)

# Tab 2: Customer Value
with tab2:
    st.subheader("Customer Long-Term Value (LTV) Analysis")
    
    client_summary = filtered_df.groupby("Client Type").agg(
        Total_Revenue=("Revenue", "sum"),
        Total_Ad_Spend=("Ad Spend", "sum"),
        Total_Conversions=("Conversions", "sum"),
        Avg_Order_Value=("Revenue", "mean")
    ).reindex(CLIENT_ORDER).dropna().reset_index()
    
    client_summary["ROAS"] = client_summary["Total_Revenue"] / client_summary["Total_Ad_Spend"]
    
    fig_client = px.pie(
        client_summary,
        names="Client Type",
        values="Total_Revenue",
        title="Revenue Share by Client Segment",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig_client, use_container_width=True)
    
    st.dataframe(client_summary.style.format({
        "Total_Revenue": "${:,.2f}",
        "Total_Ad_Spend": "${:,.2f}",
        "Avg_Order_Value": "${:,.2f}",
        "ROAS": "{:.2f}x"
    }), use_container_width=True)

# Tab 3: Timing & Seasonality
with tab3:
    st.subheader("Timing & Seasonal Delivery Optimization")
    
    time_summary = filtered_df.groupby("Time").agg(
        Total_Revenue=("Revenue", "sum"),
        Total_Conversions=("Conversions", "sum")
    ).reindex(TIME_ORDER).dropna().reset_index()
    
    fig_time = px.line(
        time_summary,
        x="Time",
        y="Total_Revenue",
        markers=True,
        title="Revenue Trend Across Time of Day",
        line_shape="spline"
    )
    st.plotly_chart(fig_time, use_container_width=True)

# Tab 4: Recommendations
with tab4:
    st.subheader("💡 Strategic Business Recommendations")
    st.markdown("""
    1. **Ad Budget Allocation:** Prioritize marketing spend on high-performing services with the strongest **ROAS** and conversion efficiency.
    2. **Customer Retention:** Focus on nurturing **Loyal** and **Returning** customer segments as they drive sustainable long-term revenue at lower overall CPAs.
    3. **Operational Peak Optimization:** Align technician scheduling and promotional campaigns with peak hours of the day to maximize conversion probability.
    """)
