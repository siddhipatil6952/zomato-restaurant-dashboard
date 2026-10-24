import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Dining Through Data | Zomato Dashboard",
    page_icon="🍽️",
    layout="wide",
)

st.title("🍽️ Dining Through Data")
st.subheader("Zomato Restaurant Analysis Dashboard")
st.caption("Explore restaurant ratings, locations, pricing, cuisines, online ordering and table booking.")

REQUIRED_COLUMNS = [
    "name", "online_order", "book_table", "rating", "votes",
    "location", "rest_type", "dish_liked", "cuisines", "approx_cost", "type"
]

@st.cache_data
def load_csv(file):
    data = pd.read_csv(file)
    data.columns = (
        data.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")
    )
    return data

def clean_data(data):
    data = data.copy()
    for col in ["name", "online_order", "book_table", "location", "rest_type", "dish_liked", "cuisines", "type"]:
        if col in data.columns:
            data[col] = data[col].astype("string").str.strip()
    for col in ["rating", "votes", "approx_cost"]:
        if col in data.columns:
            data[col] = pd.to_numeric(
                data[col].astype(str).str.replace(",", "", regex=False).str.extract(r"(-?\d+\.?\d*)")[0],
                errors="coerce"
            )
    if "name" in data.columns:
        data = data.drop_duplicates()
    return data

with st.sidebar:
    st.header("⚙️ Dashboard Controls")
    uploaded_file = st.file_uploader("Upload your Zomato CSV (optional)", type=["csv"])
    st.caption("If no file is uploaded, the app reads `zomatocleaned.csv` from the project folder.")
    st.divider()

try:
    if uploaded_file is not None:
        raw_df = load_csv(uploaded_file)
    else:
        data_path = Path(__file__).parent / "zomatocleaned.csv"
        if not data_path.exists():
            st.info("Upload your `zomatocleaned.csv` file in the sidebar, or add it beside app.py in your GitHub repository.")
            st.stop()
        raw_df = load_csv(data_path)
except Exception as exc:
    st.error(f"Could not read the CSV file: {exc}")
    st.stop()

missing_required = [c for c in REQUIRED_COLUMNS if c not in raw_df.columns]
if missing_required:
    st.error("Some expected columns are missing: " + ", ".join(missing_required))
    st.write("Columns found in your file:", list(raw_df.columns))
    st.stop()

df = clean_data(raw_df)
if df.empty:
    st.warning("The dataset is empty.")
    st.stop()

with st.sidebar:
    st.subheader("Filter Restaurants")
    locations = sorted(df["location"].dropna().astype(str).unique().tolist())
    selected_locations = st.multiselect("Location", locations, default=[])
    rating_min = float(df["rating"].min()) if df["rating"].notna().any() else 0.0
    rating_max = float(df["rating"].max()) if df["rating"].notna().any() else 5.0
    if rating_min == rating_max:
        rating_min, rating_max = 0.0, max(5.0, rating_max)
    rating_range = st.slider("Rating range", min_value=rating_min, max_value=rating_max,
                             value=(rating_min, rating_max), step=0.1)
    order_options = sorted(df["online_order"].dropna().astype(str).unique().tolist())
    selected_order = st.multiselect("Online order", order_options, default=[])
    booking_options = sorted(df["book_table"].dropna().astype(str).unique().tolist())
    selected_booking = st.multiselect("Table booking", booking_options, default=[])
    search_name = st.text_input("Search restaurant name")

filtered = df.copy()
if selected_locations:
    filtered = filtered[filtered["location"].astype(str).isin(selected_locations)]
filtered = filtered[filtered["rating"].isna() | filtered["rating"].between(rating_range[0], rating_range[1])]
if selected_order:
    filtered = filtered[filtered["online_order"].astype(str).isin(selected_order)]
if selected_booking:
    filtered = filtered[filtered["book_table"].astype(str).isin(selected_booking)]
if search_name.strip():
    filtered = filtered[filtered["name"].astype(str).str.contains(search_name.strip(), case=False, na=False)]

st.markdown("### 📌 Key Performance Indicators")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Restaurant Records", f"{len(filtered):,}")
k2.metric("Unique Restaurants", f"{filtered['name'].nunique():,}")
k3.metric("Average Rating", f"{filtered['rating'].mean():.2f}" if filtered["rating"].notna().any() else "N/A")
k4.metric("Average Cost for Two", f"₹{filtered['approx_cost'].mean():,.0f}" if filtered["approx_cost"].notna().any() else "N/A")

k5, k6, k7, k8 = st.columns(4)
k5.metric("Total Votes", f"{filtered['votes'].fillna(0).sum():,.0f}")
k6.metric("Online Ordering: Yes", f"{(filtered['online_order'].str.lower() == 'yes').sum():,}")
k7.metric("Table Booking: Yes", f"{(filtered['book_table'].str.lower() == 'yes').sum():,}")
k8.metric("Locations", f"{filtered['location'].nunique():,}")

st.divider()
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "⭐ Ratings & Services", "🍜 Cuisine & Cost", "📋 Restaurant Data"])

with tab1:
    left, right = st.columns(2)
    with left:
        loc_counts = filtered["location"].value_counts().head(10).rename_axis("Location").reset_index(name="Restaurants")
        st.plotly_chart(px.bar(loc_counts, x="Restaurants", y="Location", orientation="h",
                               title="Top 10 Locations by Restaurant Count", color="Restaurants",
                               template="plotly_white"), use_container_width=True)
    with right:
        type_counts = filtered["rest_type"].fillna("Unknown").value_counts().head(10).rename_axis("Restaurant Type").reset_index(name="Count")
        st.plotly_chart(px.bar(type_counts, x="Restaurant Type", y="Count",
                               title="Top 10 Restaurant Types", template="plotly_white"), use_container_width=True)
    left, right = st.columns(2)
    with left:
        online_counts = filtered["online_order"].fillna("Unknown").value_counts().rename_axis("Online Order").reset_index(name="Count")
        st.plotly_chart(px.pie(online_counts, names="Online Order", values="Count",
                               title="Online Ordering Availability", hole=0.35), use_container_width=True)
    with right:
        booking_counts = filtered["book_table"].fillna("Unknown").value_counts().rename_axis("Table Booking").reset_index(name="Count")
        st.plotly_chart(px.pie(booking_counts, names="Table Booking", values="Count",
                               title="Table Booking Availability", hole=0.35), use_container_width=True)

with tab2:
    left, right = st.columns(2)
    with left:
        ratings = filtered["rating"].dropna()
        if not ratings.empty:
            st.plotly_chart(px.histogram(filtered.dropna(subset=["rating"]), x="rating", nbins=20,
                                         title="Restaurant Rating Distribution", template="plotly_white"),
                            use_container_width=True)
        else:
            st.info("No rating values are available for these filters.")
    with right:
        online_rating = filtered.groupby("online_order", dropna=False)["rating"].mean().reset_index()
        online_rating["online_order"] = online_rating["online_order"].fillna("Unknown")
        st.plotly_chart(px.bar(online_rating, x="online_order", y="rating",
                               title="Average Rating by Online Ordering", labels={"online_order":"Online Order", "rating":"Average Rating"},
                               template="plotly_white"), use_container_width=True)
    scatter_df = filtered.dropna(subset=["rating", "votes"])
    if not scatter_df.empty:
        st.plotly_chart(px.scatter(scatter_df, x="votes", y="rating", color="online_order",
                                   hover_name="name", title="Ratings vs Customer Votes",
                                   labels={"votes":"Customer Votes", "rating":"Rating"},
                                   template="plotly_white"), use_container_width=True)

with tab3:
    left, right = st.columns(2)
    with left:
        cuisine_counts = filtered["cuisines"].dropna().value_counts().head(10).rename_axis("Cuisine Combination").reset_index(name="Restaurants")
        st.plotly_chart(px.bar(cuisine_counts, x="Restaurants", y="Cuisine Combination", orientation="h",
                               title="Top 10 Cuisine Combinations", template="plotly_white"),
                        use_container_width=True)
    with right:
        cost_df = filtered.dropna(subset=["approx_cost"])
        if not cost_df.empty:
            st.plotly_chart(px.histogram(cost_df, x="approx_cost", nbins=30,
                                         title="Approximate Cost for Two", labels={"approx_cost":"Cost for Two (₹)"},
                                         template="plotly_white"), use_container_width=True)
        else:
            st.info("No cost values are available for these filters.")
    location_rating = (filtered.dropna(subset=["rating"])
                       .groupby("location")["rating"].mean()
                       .sort_values(ascending=False).head(10).reset_index())
    if not location_rating.empty:
        st.plotly_chart(px.bar(location_rating, x="location", y="rating",
                               title="Top 10 Locations by Average Rating",
                               labels={"location":"Location", "rating":"Average Rating"},
                               template="plotly_white"), use_container_width=True)

with tab4:
    st.write(f"Showing **{len(filtered):,}** records after applying filters.")
    display_cols = ["name", "location", "rating", "votes", "approx_cost", "online_order", "book_table", "rest_type", "cuisines", "type"]
    st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True)
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download filtered data as CSV", data=csv_bytes,
                       file_name="zomato_filtered_data.csv", mime="text/csv")

with st.expander("🧹 Data Quality Summary"):
    q1, q2, q3 = st.columns(3)
    q1.metric("Rows in source file", f"{len(raw_df):,}")
    q2.metric("Duplicate rows removed", f"{len(raw_df) - len(df):,}")
    q3.metric("Columns", f"{df.shape[1]}")
    missing = df.isna().sum().sort_values(ascending=False)
    missing_df = missing[missing > 0].rename("Missing Values").reset_index().rename(columns={"index":"Column"})
    if missing_df.empty:
        st.success("No missing values found after numeric conversion.")
    else:
        st.dataframe(missing_df, use_container_width=True, hide_index=True)

st.caption("Project: Dining Through Data — Zomato Restaurant Analysis | Built with Python, Pandas, Streamlit and Plotly.")
