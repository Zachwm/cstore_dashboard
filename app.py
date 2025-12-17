import streamlit as st
import polars as pl
import calendar
import plotly.express as px
import plotly.graph_objects as go
from great_tables import GT
import gcsfs

st.set_page_config(page_title="Cstore Dashboard", layout="wide")
st.title("Cstore Dashboard - Idaho Stores")

# Load Data
@st.cache_data
def load_data():
    fs = gcsfs.GCSFileSystem(project="vibrant-keyword-481505-f4")
    with fs.open("gs://cstore_sample_dashboard_data/cstore_idaho.csv") as f:
        df = pl.read_csv(
            f,
            try_parse_dates=True,
            schema_overrides={
                "TRANSACTION_ITEM_ID": pl.Utf8,
                "TRANSACTION_SET_ID": pl.Utf8,
                "STORE_ID": pl.Utf8,
                "GTIN": pl.Utf8
            }
        )
    return df

try:
    print("Starting to load CSV from GCS...")
    df = load_data()
    print("CSV loaded successfully")
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()


# Sidebar filters
st.sidebar.header("Filters")

store_options = sorted(df.select("STORE_NAME").unique().to_series().to_list())
store_choice = st.sidebar.selectbox("Select Store", store_options)

months = (
    df.select(pl.col("TRANSACTION_DATE").dt.month().alias("month"))
    .unique()
    .sort("month")
    .to_series()
    .to_list()
)

min_month = min(months)
max_month = max(months)
month_range = st.sidebar.slider(
    "Select Month Range",
    min_value=min_month,
    max_value=max_month,
    value=(min_month, max_month)
)

st.sidebar.caption(f"{calendar.month_abbr[month_range[0]]} - {calendar.month_abbr[month_range[1]]}")

month_choice = list(range(month_range[0], month_range[1] + 1))

df_filtered = df.filter(
    (pl.col("STORE_NAME") == store_choice) &
    (pl.col("TRANSACTION_DATE").dt.month().is_in(month_choice))
)

st.sidebar.metric("Total Transactions", f"{df_filtered.height:,}")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Top Products (Weekly)",
    "Beverage Brands",
    "Cash vs Credit",
    "Demographics"
])

# Tab 1: Top 5 Products by Week

with tab1:
    st.header("Top 5 Products (Excluding Fuels) - Weekly Analysis")
    
    col1, col2 = st.columns(2)
    
    weekly_products = (
        df_filtered
        .filter(
            (pl.col("CATEGORY") != "Fuel") &
            (pl.col("ITEM_NAME").is_not_null()) &
            (pl.col("ITEM_NAME") != "") &
            (pl.col("ITEM_NAME") != "null")
        )
        .with_columns(
            pl.col("TRANSACTION_DATE").dt.truncate("1w").alias("WEEK")
        )
        .group_by(["WEEK", "ITEM_NAME"])
        .agg(pl.sum("QUANTITY").alias("Total_Sold"))
        .sort(["WEEK", "Total_Sold"], descending=[False, True])
    )
    
    top_products_overall = (
        df_filtered
        .filter(
            (pl.col("CATEGORY") != "Fuel") &
            (pl.col("ITEM_NAME").is_not_null()) &
            (pl.col("ITEM_NAME") != "") &
            (pl.col("ITEM_NAME") != "null")
        )
        .group_by("ITEM_NAME")
        .agg(pl.sum("QUANTITY").alias("Total_Sold"))
        .sort("Total_Sold", descending=True)
        .head(5)
    )
    
    with col1:
        if top_products_overall.height > 0:
            st.metric("Top Product Overall", top_products_overall[0, "ITEM_NAME"])
    with col2:
        if top_products_overall.height > 0:
            st.metric("Quantity Sold", f"{top_products_overall[0, 'Total_Sold']:,}")
    
    with st.expander("View Detailed Weekly Breakdown", expanded=False):
        st.dataframe(weekly_products.to_pandas(), width="stretch")
    
    st.subheader("Overall Top 5 Products Summary")
    if top_products_overall.height > 0:
        gt_table = (
            GT(top_products_overall.to_pandas())
            .tab_header(
                title="Top 5 Products",
                subtitle="Excluding Fuel Products"
            )
            .fmt_number(columns="Total_Sold", decimals=0, use_seps=True)
            .cols_label(
                ITEM_NAME="Product Name",
                Total_Sold="Total Quantity Sold"
            )
        )
        st.html(gt_table.as_raw_html())
        
        df_top_pd = top_products_overall.to_pandas()
        fig = px.bar(df_top_pd, x='ITEM_NAME', y='Total_Sold',
                    title='Top 5 Products Sold',
                    labels={'ITEM_NAME': 'Product Name', 'Total_Sold': 'Total Quantity Sold'},
                    color_discrete_sequence=['#1f77b4'])
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, width="stretch")
    else:
        st.warning("No products found with current filters")

# Tab 2: Packaged Beverage Brands

with tab2:
    st.header("Packaged Beverage Brands Analysis")
    
    beverages = df_filtered.filter(
        (pl.col("CATEGORY").str.contains("Beverage")) &
        (pl.col("BRAND").is_not_null()) &
        (pl.col("BRAND") != "") &
        (pl.col("BRAND") != "null")
    )
    
    if beverages.height > 0:
        with st.container():
            metric_cols = st.columns(3)
            total_bev_sales = beverages.select(pl.sum("TOTAL_SALE")).item()
            total_bev_quantity = beverages.select(pl.sum("QUANTITY")).item()
            unique_brands = beverages.select(pl.n_unique("BRAND")).item()
            
            with metric_cols[0]:
                st.metric("Total Beverage Sales", f"${total_bev_sales:,.2f}")
            with metric_cols[1]:
                st.metric("Total Quantity", f"{total_bev_quantity:,}")
            with metric_cols[2]:
                st.metric("Unique Brands", f"{unique_brands}")
        
        brand_sales = (
            beverages.group_by("BRAND")
            .agg([
                pl.sum("QUANTITY").alias("Total_Quantity"),
                pl.sum("TOTAL_SALE").alias("Total_Sales")
            ])
            .sort("Total_Quantity", descending=True)
        )
        
        subtab1, subtab2 = st.tabs(["By Quantity", "By Revenue"])
        
        with subtab1:
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("Top 10 Brands")
                gt_brand_qty = (
                    GT(brand_sales.head(10).to_pandas())
                    .tab_header(title="Top 10 Beverage Brands by Quantity")
                    .fmt_number(columns="Total_Quantity", decimals=0, use_seps=True)
                    .fmt_currency(columns="Total_Sales", currency="USD")
                    .cols_label(
                        BRAND="Brand",
                        Total_Quantity="Quantity Sold",
                        Total_Sales="Revenue"
                    )
                )
                st.html(gt_brand_qty.as_raw_html())
                
                df_brand_pd = brand_sales.head(10).to_pandas()
                fig = px.bar(df_brand_pd, x='BRAND', y='Total_Quantity',
                            title='Top 10 Beverage Brands by Quantity',
                            labels={'BRAND': 'Brand', 'Total_Quantity': 'Total Quantity Sold'},
                            color_discrete_sequence=['#ff7f0e'])
                fig.update_layout(xaxis_tickangle=-45, height=400)
                st.plotly_chart(fig, width="stretch")
            
            with col_right:
                st.subheader("Bottom 10 Brands")
                bottom_brands = brand_sales.tail(10).sort("Total_Quantity", descending=False)
                gt_brand_bottom = (
                    GT(bottom_brands.to_pandas())
                    .tab_header(title="Bottom 10 Beverage Brands by Quantity")
                    .fmt_number(columns="Total_Quantity", decimals=0, use_seps=True)
                    .fmt_currency(columns="Total_Sales", currency="USD")
                    .cols_label(
                        BRAND="Brand",
                        Total_Quantity="Quantity Sold",
                        Total_Sales="Revenue"
                    )
                )
                st.html(gt_brand_bottom.as_raw_html())
                
                df_bottom_pd = bottom_brands.to_pandas()
                fig = px.bar(df_bottom_pd, x='BRAND', y='Total_Quantity',
                            title='Bottom 10 Beverage Brands by Quantity',
                            labels={'BRAND': 'Brand', 'Total_Quantity': 'Total Quantity Sold'},
                            color_discrete_sequence=['#d62728'])
                fig.update_layout(xaxis_tickangle=-45, height=400)
                st.plotly_chart(fig, width="stretch")
        
        with subtab2:
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("Top 10 Brands")
                brand_sales_sorted = brand_sales.sort("Total_Sales", descending=True)
                
                gt_brand_rev = (
                    GT(brand_sales_sorted.head(10).to_pandas())
                    .tab_header(title="Top 10 Beverage Brands by Revenue")
                    .fmt_currency(columns="Total_Sales", currency="USD")
                    .fmt_number(columns="Total_Quantity", decimals=0, use_seps=True)
                    .cols_label(
                        BRAND="Brand",
                        Total_Quantity="Quantity Sold",
                        Total_Sales="Revenue"
                    )
                )
                st.html(gt_brand_rev.as_raw_html())
                
                df_brand_rev_pd = brand_sales_sorted.head(10).to_pandas()
                fig = px.bar(df_brand_rev_pd, x='BRAND', y='Total_Sales',
                            title='Top 10 Beverage Brands by Revenue',
                            labels={'BRAND': 'Brand', 'Total_Sales': 'Total Sales ($)'},
                            color_discrete_sequence=['#2ca02c'])
                fig.update_layout(xaxis_tickangle=-45, height=400)
                st.plotly_chart(fig, width="stretch")
            
            with col_right:
                st.subheader("Bottom 10 Brands")
                bottom_brands_rev = brand_sales_sorted.tail(10).sort("Total_Sales", descending=False)
                
                gt_brand_bottom_rev = (
                    GT(bottom_brands_rev.to_pandas())
                    .tab_header(title="Bottom 10 Beverage Brands by Revenue")
                    .fmt_currency(columns="Total_Sales", currency="USD")
                    .fmt_number(columns="Total_Quantity", decimals=0, use_seps=True)
                    .cols_label(
                        BRAND="Brand",
                        Total_Quantity="Quantity Sold",
                        Total_Sales="Revenue"
                    )
                )
                st.html(gt_brand_bottom_rev.as_raw_html())
                
                df_bottom_rev_pd = bottom_brands_rev.to_pandas()
                fig = px.bar(df_bottom_rev_pd, x='BRAND', y='Total_Sales',
                            title='Bottom 10 Beverage Brands by Revenue',
                            labels={'BRAND': 'Brand', 'Total_Sales': 'Total Sales ($)'},
                            color_discrete_sequence=['#d62728'])
                fig.update_layout(xaxis_tickangle=-45, height=400)
                st.plotly_chart(fig, width="stretch")
    else:
        st.warning("No beverage products found with current filters")

# Tab 3: Cash vs Credit

with tab3:
    st.header("Cash vs Credit Comparison")
    
    payment_summary = (
        df_filtered
        .filter(
            (pl.col("PAYMENT_TYPE") == "CASH") |
            (pl.col("PAYMENT_TYPE") == "CREDIT") |
            (pl.col("PAYMENT_TYPE") == "EBT") |
            (pl.col("PAYMENT_TYPE") == "DEBIT")
        )
        .group_by("PAYMENT_TYPE")
        .agg([
            pl.sum("TOTAL_SALE").alias("Total_Sales"),
            pl.sum("QUANTITY").alias("Total_Items"),
            pl.len().alias("Transaction_Count")
        ])
    )
    
    cols = st.columns(len(payment_summary))
    for idx, row in enumerate(payment_summary.iter_rows(named=True)):
        with cols[idx]:
            st.metric(
                row["PAYMENT_TYPE"],
                f"${row['Total_Sales']:,.2f}",
                f"{row['Total_Items']:,} items"
            )
    
    gt_payment = (
        GT(payment_summary.to_pandas())
        .tab_header(title="Payment Type Summary")
        .fmt_currency(columns="Total_Sales", currency="USD")
        .fmt_number(columns=["Total_Items", "Transaction_Count"], decimals=0, use_seps=True)
        .cols_label(
            PAYMENT_TYPE="Payment Type",
            Total_Sales="Total Sales",
            Total_Items="Total Items",
            Transaction_Count="# Transactions"
        )
    )
    st.html(gt_payment.as_raw_html())
    
    with st.expander("View Weekly Payment Trends", expanded=True):
        st.subheader("Sales Target Threshold")
        st.caption("Set a weekly sales target to compare payment type performance against your goal")
        
        weekly_payment_preview = (
            df_filtered
            .filter(
                (pl.col("PAYMENT_TYPE") == "CASH") |
                (pl.col("PAYMENT_TYPE") == "CREDIT") |
                (pl.col("PAYMENT_TYPE") == "EBT") |
                (pl.col("PAYMENT_TYPE") == "DEBIT")
            )
            .with_columns(
                pl.col("TRANSACTION_DATE").dt.truncate("1w").alias("WEEK")
            )
            .group_by(["WEEK", "PAYMENT_TYPE"])
            .agg(pl.sum("TOTAL_SALE").alias("Total_Sales"))
        )
        
        if weekly_payment_preview.height > 0:
            min_sales = float(weekly_payment_preview.select(pl.col("Total_Sales").min()).item())
            max_sales = float(weekly_payment_preview.select(pl.col("Total_Sales").max()).item())
            avg_sales = float(weekly_payment_preview.select(pl.col("Total_Sales").mean()).item())
            
            target_line = st.slider(
                "Weekly Sales Target ($)",
                min_value=int(min_sales),
                max_value=int(max_sales),
                value=int(avg_sales),
                step=1000,
                format="$%d"
            )
        
        weekly_payment = (
            df_filtered
            .filter(
                (pl.col("PAYMENT_TYPE") == "CASH") |
                (pl.col("PAYMENT_TYPE") == "CREDIT") |
                (pl.col("PAYMENT_TYPE") == "EBT") |
                (pl.col("PAYMENT_TYPE") == "DEBIT")
            )
            .with_columns(
                pl.col("TRANSACTION_DATE").dt.truncate("1w").alias("WEEK")
            )
            .group_by(["WEEK", "PAYMENT_TYPE"])
            .agg(pl.sum("TOTAL_SALE").alias("Total_Sales"))
            .sort("WEEK")
        )
        
        df_weekly_pd = weekly_payment.to_pandas()
        df_weekly_pd['WEEK'] = df_weekly_pd['WEEK'].astype(str)
        
        fig = px.line(df_weekly_pd, x='WEEK', y='Total_Sales', color='PAYMENT_TYPE',
                     title='Weekly Sales by Payment Type',
                     labels={'WEEK': 'Week', 'Total_Sales': 'Total Sales ($)', 'PAYMENT_TYPE': 'Payment Type'},
                     markers=True)
        
        fig.add_hline(y=target_line, line_dash="dash", line_color="red", 
                     annotation_text=f"Target: ${target_line:,.0f}",
                     annotation_position="right")
        
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, width="stretch")
    
    st.subheader("Most Purchased Items by Payment Type")
    st.caption("Top 10 items for each payment method (excluding fuel)")
    
    top_items_by_payment = (
        df_filtered
        .filter(
            (pl.col("PAYMENT_TYPE").is_in(["CASH", "CREDIT", "EBT", "DEBIT"])) &
            (pl.col("CATEGORY") != "Fuel") &
            (pl.col("ITEM_NAME").is_not_null()) &
            (pl.col("ITEM_NAME") != "") &
            (pl.col("ITEM_NAME") != "null")
        )
        .group_by(["PAYMENT_TYPE", "ITEM_NAME"])
        .agg(pl.sum("QUANTITY").alias("Total_Quantity"))
        .sort(["PAYMENT_TYPE", "Total_Quantity"], descending=[False, True])
    )
    
    # Get top 10 items per payment type
    top_10_per_payment = (
        top_items_by_payment
        .with_columns(
            pl.col("Total_Quantity").rank("dense", descending=True).over("PAYMENT_TYPE").alias("rank")
        )
        .filter(pl.col("rank") <= 10)
        .drop("rank")
    )
    
    # Create a 2x2 grid for the payment types
    payment_types = top_10_per_payment.select("PAYMENT_TYPE").unique().sort("PAYMENT_TYPE").to_series().to_list()
    
    cols_per_row = 2
    num_rows = (len(payment_types) + cols_per_row - 1) // cols_per_row
    
    for row_idx in range(num_rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            payment_idx = row_idx * cols_per_row + col_idx
            if payment_idx < len(payment_types):
                payment_type = payment_types[payment_idx]
                
                payment_data = (
                    top_10_per_payment
                    .filter(pl.col("PAYMENT_TYPE") == payment_type)
                    .sort("Total_Quantity", descending=False)
                    .to_pandas()
                )
                
                with cols[col_idx]:
                    color_map = {'CASH': '#2ca02c', 'CREDIT': '#1f77b4', 'DEBIT': '#ff7f0e', 'EBT': '#d62728'}
                    fig = px.bar(payment_data, 
                                 x='Total_Quantity', 
                                 y='ITEM_NAME',
                                 title=f'{payment_type}',
                                 labels={'ITEM_NAME': 'Product', 'Total_Quantity': 'Quantity'},
                                 height=400,
                                 color_discrete_sequence=[color_map.get(payment_type, '#1f77b4')])
                    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig, use_container_width=True)

# Tab 4: Census Data

with tab4:
    st.header("Store Demographics & Census Data")
    
    with st.container():
        st.subheader("Location Information")
        demo_cols = ["state_fips", "county_fips", "tract"]
        available_demo_cols = [col for col in demo_cols if col in df_filtered.columns]
        
        if available_demo_cols:
            unique_locations = df_filtered.select(available_demo_cols).unique()
            st.dataframe(unique_locations.to_pandas(), width="stretch")
    
    with st.expander("American Community Survey (ACS) Variables", expanded=True):
        # ACS variables
        acs_variables = [
            "median_family_income",
            "median_income_by_earners",
            "number_of_earners",
            "median_income_with_children",
            "household_type_population",
            "population",
            "median_age",
            "unemployed",
            "housing_units",
            "bachelors_degree_count"
        ]
        
        available_acs = [col for col in acs_variables if col in df_filtered.columns]
        
        if available_acs and len(available_acs) >= 10:
            acs_data = df_filtered.select(available_acs).unique()
            
            acs_pd = acs_data.to_pandas()
            gt_acs = (
                GT(acs_pd)
                .tab_header(
                    title="Census Demographic Data",
                    subtitle="American Community Survey Variables"
                )
                .fmt_number(
                    columns=[c for c in available_acs if c in acs_pd.columns],
                    decimals=0,
                    use_seps=True
                )
                .cols_label(
                    median_family_income="Median Family Income",
                    median_income_by_earners="Median Income by Earners",
                    number_of_earners="Number of Earners",
                    median_income_with_children="Median Income (with Children)",
                    household_type_population="Household Type Population",
                    population="Total Population",
                    median_age="Median Age",
                    unemployed="Unemployed Count",
                    housing_units="Housing Units",
                    bachelors_degree_count="Bachelor's Degree Count"
                )
            )
            st.html(gt_acs.as_raw_html())
        else:
            st.warning(f"""
            **{len(available_acs)} ACS variables found**
            """)