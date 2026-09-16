from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Singapore Jobs Dashboard",
    page_icon="📊",
    layout="wide"
)

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR
THRESHOLD = 3.0


@st.cache_data
def load_data():
    all_data = pd.read_csv(PROJECT_DIR / "SGJobData.csv")
    it_data = pd.read_csv(PROJECT_DIR / "jobs_clean.csv")

    # Match the notebook cleaning steps
    all_data = all_data.dropna(subset=["title"]).copy()

    it_data = it_data[
        it_data["salary_analysis_ready"]
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("TRUE")
    ].copy()

    all_data["dataset"] = "All Industries"
    it_data["dataset"] = "IT"

    return all_data, it_data


def summarize(data):
    data = data.dropna(subset=["employmentTypes"])

    summary = (
        data["employmentTypes"]
        .value_counts()
        .rename_axis("employmentTypes")
        .reset_index(name="count")
    )

    summary["percentage"] = (
        summary["count"] / summary["count"].sum() * 100
    )

    summary["group"] = summary["employmentTypes"].where(
        summary["percentage"] >= THRESHOLD,
        "Other"
    )

    grouped = (
        summary.groupby("group", as_index=False)["count"]
        .sum()
    )

    grouped["percentage"] = (
        grouped["count"] / grouped["count"].sum() * 100
    ).round(1)

    return grouped


df_all, df_it = load_data()

st.title("Singapore Employment Type Dashboard")
st.caption(
    "Interactive comparison of employment types across all industries and IT postings."
)

# Sidebar controls
st.sidebar.header("Dashboard Controls")

selected_datasets = st.sidebar.multiselect(
    "Select dataset",
    options=["All Industries", "IT"],
    default=["All Industries", "IT"]
)

if not selected_datasets:
    st.warning("Select at least one dataset.")
    st.stop()

# Create summaries
summaries = []

if "All Industries" in selected_datasets:
    all_summary = summarize(df_all)
    all_summary["dataset"] = "All Industries"
    summaries.append(all_summary)

if "IT" in selected_datasets:
    it_summary = summarize(df_it)
    it_summary["dataset"] = "IT"
    summaries.append(it_summary)

combined = pd.concat(summaries, ignore_index=True)

# Consistent category order
category_order = [
    "Other",
    "Contract",
    "Full Time",
    "Permanent"
]

combined["group"] = pd.Categorical(
    combined["group"],
    categories=category_order,
    ordered=True
)

combined = combined.sort_values("group")

# KPI cards
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "All-industry postings",
        f"{len(df_all):,}"
    )

with col2:
    st.metric(
        "IT postings",
        f"{len(df_it):,}"
    )

with col3:
    st.metric(
        "Categories grouped as Other below",
        f"{THRESHOLD:.0f}%"
    )

# Interactive chart
fig = px.bar(
    combined,
    x="percentage",
    y="group",
    color="dataset",
    barmode="group",
    orientation="h",
    text=combined["percentage"].astype(str) + "%",
    labels={
        "percentage": "% of postings",
        "group": "Employment type",
        "dataset": ""
    },
    color_discrete_map={
        "All Industries": "#4C6EF5",
        "IT": "#12877F"
    },
    title="Employment Type Mix"
)

fig.update_traces(
    textposition="outside",
    cliponaxis=False
)

fig.update_layout(
    xaxis=dict(
        title="% of postings",
        range=[0, max(combined["percentage"]) * 1.2],
        ticksuffix="%"
    ),
    yaxis_title=None,
    plot_bgcolor="white",
    paper_bgcolor="white",
    legend_title=None,
    margin=dict(
        l=20,
        r=100,
        t=80,
        b=50
    ),
    height=550
)

st.plotly_chart(fig, use_container_width=True)

# Explanation
st.info(
    "Employment types representing less than 3% of postings are grouped "
    "under 'Other', matching the analysis in the notebook."
)

# Summary table
st.subheader("Summary table")

table = combined.pivot(
    index="group",
    columns="dataset",
    values=["count", "percentage"]
).fillna(0)

st.dataframe(
    table.style.format("{:.1f}"),
    use_container_width=True
)

# Download summary
st.download_button(
    label="Download summary CSV",
    data=combined.to_csv(index=False),
    file_name="employment_type_summary.csv",
    mime="text/csv"
)