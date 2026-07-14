"""
Global Superstore — Interactive Business Dashboard
----------------------------------------------------
Run locally with:
    streamlit run app.py

Expects a cleaned CSV at data/Global_Superstore_clean.csv (produced by
notebook/Global_Superstore_Analysis.ipynb). Falls back to cleaning the
raw file on the fly if the cleaned file isn't found.
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="Global Superstore Dashboard",
    page_icon="📊",
    layout="wide",
)

RAW_PATH = "data/Global_Superstore.csv"
CLEAN_PATH = "data/Global_Superstore_clean.csv"


@st.cache_data
def load_data():
    try:
        df = pd.read_csv(CLEAN_PATH, parse_dates=["Order Date", "Ship Date"])
    except FileNotFoundError:
        # Fallback: clean the raw file the same way the notebook does
        df = pd.read_csv(RAW_PATH, parse_dates=["Order Date", "Ship Date"])
        df = df.drop_duplicates()
        df["Customer Name"] = df["Customer Name"].fillna("Unknown Customer")
        df["Sales"] = df["Sales"].abs()
        df["Sales"] = df.groupby("Sub-Category")["Sales"].transform(
            lambda s: s.fillna(s.median())
        )
        for c in ["Ship Mode", "Segment", "Country", "State", "Region",
                  "Category", "Sub-Category", "Customer Name"]:
            df[c] = df[c].astype(str).str.strip()
        df["Profit Margin"] = (df["Profit"] / df["Sales"]).replace(
            [np.inf, -np.inf], 0
        )
        df["Order Month"] = df["Order Date"].dt.to_period("M").astype(str)
    return df


df = load_data()

# ---------------------------------------------------------------- SIDEBAR --
st.sidebar.title("🔎 Filters")

regions = sorted(df["Region"].unique())
sel_regions = st.sidebar.multiselect("Region", regions, default=regions)

cat_pool = df[df["Region"].isin(sel_regions)] if sel_regions else df
categories = sorted(cat_pool["Category"].unique())
sel_categories = st.sidebar.multiselect("Category", categories, default=categories)

subcat_pool = cat_pool[cat_pool["Category"].isin(sel_categories)] if sel_categories else cat_pool
subcategories = sorted(subcat_pool["Sub-Category"].unique())
sel_subcategories = st.sidebar.multiselect(
    "Sub-Category", subcategories, default=subcategories
)

date_min, date_max = df["Order Date"].min(), df["Order Date"].max()
date_range = st.sidebar.date_input(
    "Order Date range", value=(date_min, date_max), min_value=date_min, max_value=date_max
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data: Global Superstore dataset. Use the filters above to slice Sales, "
    "Profit, and Top Customer KPIs below."
)

# ---------------------------------------------------------------- FILTER ---
mask = (
    df["Region"].isin(sel_regions if sel_regions else regions)
    & df["Category"].isin(sel_categories if sel_categories else categories)
    & df["Sub-Category"].isin(sel_subcategories if sel_subcategories else subcategories)
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    mask &= df["Order Date"].between(start, end)

fdf = df[mask]

# ------------------------------------------------------------------ HEAD ---
st.title("📊 Global Superstore — Business Performance Dashboard")
st.caption(
    "Sales, profit, and segment-wise performance analysis with interactive filters."
)

if fdf.empty:
    st.warning("No data matches the selected filters. Adjust filters in the sidebar.")
    st.stop()

# ------------------------------------------------------------------- KPIs --
total_sales = fdf["Sales"].sum()
total_profit = fdf["Profit"].sum()
margin = (total_profit / total_sales * 100) if total_sales else 0
total_orders = fdf["Order ID"].nunique()
avg_discount = fdf["Discount"].mean() * 100

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Sales", f"${total_sales:,.0f}")
k2.metric("Total Profit", f"${total_profit:,.0f}")
k3.metric("Profit Margin", f"{margin:.1f}%")
k4.metric("Orders", f"{total_orders:,}")
k5.metric("Avg. Discount", f"{avg_discount:.1f}%")

st.markdown("---")

# ------------------------------------------------------------- CHART ROW 1 -
c1, c2 = st.columns(2)

with c1:
    st.subheader("Sales & Profit Trend by Month")
    trend = fdf.groupby("Order Month")[["Sales", "Profit"]].sum().reset_index()
    trend = trend.sort_values("Order Month")
    fig = px.line(trend, x="Order Month", y=["Sales", "Profit"], markers=True)
    fig.update_layout(legend_title_text="", xaxis_title="", yaxis_title="$")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Sales by Region")
    region_sales = fdf.groupby("Region")["Sales"].sum().reset_index()
    fig = px.pie(region_sales, names="Region", values="Sales", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------- CHART ROW 2 -
c3, c4 = st.columns(2)

with c3:
    st.subheader("Profit by Sub-Category")
    subcat = fdf.groupby("Sub-Category")["Profit"].sum().sort_values().reset_index()
    fig = px.bar(
        subcat, x="Profit", y="Sub-Category", orientation="h",
        color=subcat["Profit"] > 0,
        color_discrete_map={True: "#2ca02c", False: "#d62728"},
    )
    fig.update_layout(showlegend=False, yaxis_title="", xaxis_title="Profit ($)")
    st.plotly_chart(fig, use_container_width=True)

with c4:
    st.subheader("Top 5 Customers by Sales")
    top5 = (
        fdf.groupby("Customer Name")["Sales"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .sort_values()
        .reset_index()
    )
    fig = px.bar(top5, x="Sales", y="Customer Name", orientation="h")
    fig.update_layout(yaxis_title="", xaxis_title="Sales ($)")
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------- CHART ROW 3 -
c5, c6 = st.columns(2)

with c5:
    st.subheader("Sales vs. Profit by Category")
    cat_perf = fdf.groupby("Category")[["Sales", "Profit"]].sum().reset_index()
    fig = px.bar(cat_perf, x="Category", y=["Sales", "Profit"], barmode="group")
    fig.update_layout(legend_title_text="", yaxis_title="$")
    st.plotly_chart(fig, use_container_width=True)

with c6:
    st.subheader("Discount vs. Profit Margin")
    fig = px.scatter(
        fdf, x="Discount", y="Profit Margin", color="Category",
        opacity=0.5, trendline="ols" if len(fdf) > 1 else None,
    )
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------- DATA TABLE --
st.markdown("---")
with st.expander("🔽 View filtered raw data"):
    st.dataframe(fdf, use_container_width=True)
    st.download_button(
        "Download filtered data as CSV",
        fdf.to_csv(index=False).encode("utf-8"),
        file_name="filtered_superstore_data.csv",
        mime="text/csv",
    )
