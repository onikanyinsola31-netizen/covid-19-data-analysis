import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="COVID-19 Dashboard",
    page_icon="🦠",
    layout="wide"
)

# Title
st.title("🦠 COVID-19 Data Analysis Dashboard")
st.markdown("### By Juliet Oni | Data Analyst Portfolio Project")
st.markdown("---")

# Load and CLEAN data
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
    df = pd.read_csv(url)
    
    # CRITICAL: Clean the country names
    df['Country/Region'] = df['Country/Region'].astype(str).str.strip()
    
    return df

# NEW FUNCTION: Transform to time series format
@st.cache_data
def prepare_time_series_data(df, selected_countries=None):
    """
    Simplified time series conversion
    """
    # Get all columns
    all_columns = df.columns.tolist()
    
    # Manually exclude known metadata columns
    metadata = ['Province/State', 'Country/Region', 'Lat', 'Long']
    
    # Date columns are everything else
    date_columns = [col for col in all_columns if col not in metadata]
    
    # Filter if countries selected
    if selected_countries:
        df = df[df['Country/Region'].isin(selected_countries)]
    
    # Group by country
    country_data = df.groupby('Country/Region', as_index=False)[date_columns].sum()
    
    # Melt to long format
    time_series = country_data.melt(
        id_vars=['Country/Region'],
        value_vars=date_columns,
        var_name='Date_String',
        value_name='Total_Cases'
    )
    
    # Convert dates - handle errors gracefully
    valid_dates = []
    for date_str in time_series['Date_String']:
        try:
            # Try to parse as date
            pd_date = pd.to_datetime(date_str)
            valid_dates.append(pd_date)
        except:
            # If fails, use a default date
            valid_dates.append(pd.NaT)
    
    time_series['Date'] = valid_dates
    
    # Remove rows where date conversion failed
    time_series = time_series.dropna(subset=['Date'])
    
    # Sort and calculate
    time_series = time_series.sort_values(['Country/Region', 'Date'])
    time_series['New_Cases'] = time_series.groupby('Country/Region')['Total_Cases'].diff().fillna(0)
    
    # Calculate 7-day moving average
    time_series['MA_7_Days'] = time_series.groupby('Country/Region')['New_Cases'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )
    
    return time_series

# NEW FUNCTION: Generate summary statistics
def get_summary_statistics(time_series_data):
    """
    Calculate key metrics from time series data
    """
    if time_series_data.empty:
        return pd.DataFrame()
    
    # Get latest date
    latest_date = time_series_data['Date'].max()
    Earliest_date = time_series_data['Date'].min()
    week_ago = latest_date - timedelta(days=7)
    month_ago = latest_date - timedelta(days=30)
    
    # Filter data for time periods
    latest_data = time_series_data[time_series_data['Date'] == latest_date]
    week_data = time_series_data[time_series_data['Date'] >= week_ago]
    month_data = time_series_data[time_series_data['Date'] >= month_ago]
    
    # Calculate summary by country
    summary = latest_data.groupby('Country/Region').agg({
        'Total_Cases': 'last',
        'New_Cases': 'last'
    }).reset_index()
    
    # Add weekly and monthly totals
    weekly_totals = week_data.groupby('Country/Region')['New_Cases'].sum().reset_index()
    weekly_totals.columns = ['Country/Region', 'Weekly_New_Cases']
    
    monthly_totals = month_data.groupby('Country/Region')['New_Cases'].sum().reset_index()
    monthly_totals.columns = ['Country/Region', 'Monthly_New_Cases']
    
    # Merge all summaries
    summary = pd.merge(summary, weekly_totals, on='Country/Region', how='left')
    summary = pd.merge(summary, monthly_totals, on='Country/Region', how='left')
    
    # Calculate growth rates with division by zero protection
    summary['Weekly_Growth_Rate'] = (summary['Weekly_New_Cases'] / summary['Total_Cases'].replace(0, 1) * 100).round(2)
    
    return summary

# Load data
df = load_data()

# Sidebar controls
st.sidebar.header("📊 Dashboard Controls")

# Get ALL cleaned countries
all_countries = sorted(df['Country/Region'].unique().tolist())

# Country selection
selected_countries = st.sidebar.multiselect(
    "Select Countries",
    all_countries,
    default=[],
    help="Select countries to analyze"
)

# Date range selection
st.sidebar.subheader("📅 Date Range")
min_date = pd.to_datetime('2020-01-22')
max_date = pd.to_datetime(datetime.now().strftime('%Y-%m-%d'))

start_date = st.sidebar.date_input(
    "Start Date",
    value=max_date - timedelta(days=90),
    min_value=min_date,
    max_value=max_date
)

end_date = st.sidebar.date_input(
    "End Date",
    value=max_date,
    min_value=min_date,
    max_value=max_date
)

# Analysis type
st.sidebar.subheader("📈 Analysis Type")
analysis_type = st.sidebar.radio(
    "Choose visualization:",
    ["Time Series", "Summary Statistics", "Comparison Chart", "Growth Analysis"]
)

# Prepare time series data
time_series_data = prepare_time_series_data(df, selected_countries)

# Filter by date range
if not time_series_data.empty:
    time_series_data = time_series_data[
        (time_series_data['Date'] >= pd.Timestamp(start_date)) &
        (time_series_data['Date'] <= pd.Timestamp(end_date))
    ]

# Main dashboard content
if not selected_countries:
    st.info("👆 Please select countries from the sidebar to begin analysis")
    
    # Show overall stats
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🌍 Total Countries", df['Country/Region'].nunique())
    
    with col2:
        st.metric("📊 Total Rows", len(df))
    
    with col3:
        # Find date columns more robustly
        date_cols = []
        for col in df.columns:
            if '/' in str(col):  # Check if it looks like a date
                try:
                    # Try to parse as date to confirm
                    pd.to_datetime(col)
                    date_cols.append(col)
                except:
                    pass
        
        st.metric("📅 Days of Data", len(date_cols))
    
    with col4:
        if date_cols:
            try:
                latest_date = pd.to_datetime(date_cols[-1])
                display_date = latest_date.strftime('%Y-%m-%d')
            except:
                display_date = date_cols[-1]  # Show raw string if can't parse
        else:
            display_date = "N/A"
        st.metric("Latest Date", display_date)
    
    with col5:
        if date_cols:
            try:
                earliest_date = pd.to_datetime(date_cols[0])
                display_date = earliest_date.strftime('%Y-%m-%d')
            except:
                display_date = date_cols[0]  # Show raw string if can't parse
        else:
            display_date = "N/A"
        st.metric("Earliest Date", display_date)
    
    st.subheader("📋 Raw Data Preview")
    st.dataframe(df.head(10))
    
else:
    # =================== ANALYSIS SECTION ===================
    
    if analysis_type == "Time Series":
        st.header("📈 COVID-19 Cases Over Time")
        
        # Line chart for total cases
        fig_total = px.line(
            time_series_data,
            x='Date',
            y='Total_Cases',
            color='Country/Region',
            title='Total Confirmed Cases Over Time',
            labels={'Total_Cases': 'Total Cases', 'Date': 'Date'},
            template='plotly_white'
        )
        st.plotly_chart(fig_total, use_container_width=True)
        
        # Line chart for daily new cases
        fig_daily = px.line(
            time_series_data,
            x='Date',
            y='New_Cases',
            color='Country/Region',
            title='Daily New Cases',
            labels={'New_Cases': 'New Cases', 'Date': 'Date'},
            template='plotly_white'
        )
        st.plotly_chart(fig_daily, use_container_width=True)
        
        # Moving average chart
        if 'MA_7_Days' in time_series_data.columns:
            fig_ma = px.line(
                time_series_data,
                x='Date',
                y='MA_7_Days',
                color='Country/Region',
                title='7-Day Moving Average of New Cases',
                labels={'MA_7_Days': '7-Day Moving Average', 'Date': 'Date'},
                template='plotly_white'
            )
            st.plotly_chart(fig_ma, use_container_width=True)
    
    elif analysis_type == "Summary Statistics":
        st.header("📊 Summary Statistics")
        
        # Get summary statistics
        summary_stats = get_summary_statistics(time_series_data)
        
        if not summary_stats.empty:
            # Display summary table
            st.subheader("Country-wise Summary")
            st.dataframe(
                summary_stats.style.format({
                    'Total_Cases': '{:,}',
                    'New_Cases': '{:,}',
                    'Weekly_New_Cases': '{:,}',
                    'Monthly_New_Cases': '{:,}',
                    'Weekly_Growth_Rate': '{:.2f}%'
                })
            )
            
            # Bar chart for total cases
            fig_bar = px.bar(
                summary_stats,
                x='Country/Region',
                y='Total_Cases',
                color='Country/Region',
                title='Total Cases by Country',
                text='Total_Cases',
                template='plotly_white'
            )
            fig_bar.update_traces(texttemplate='%{text:,}', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Metrics cards
            st.subheader("Key Metrics")
            cols = st.columns(min(len(selected_countries), 4))
            for idx, (col, country) in enumerate(zip(cols, selected_countries)):
                with col:
                    country_data = summary_stats[summary_stats['Country/Region'] == country]
                    if not country_data.empty:
                        st.metric(
                            label=country,
                            value=f"{country_data['Total_Cases'].values[0]:,}",
                            delta=f"{country_data['New_Cases'].values[0]:,} new cases"
                        )
        else:
            st.warning("No summary statistics available")
    
    elif analysis_type == "Comparison Chart":
        st.header("📊 Country Comparison")
        
        if not time_series_data.empty:
            # Bar chart comparison
            if len(selected_countries) >= 2:
                latest_data = time_series_data[time_series_data['Date'] == time_series_data['Date'].max()]
                
                if not latest_data.empty:
                    fig_comparison = go.Figure()
                    
                    # Add bars for different metrics
                    metrics = ['Total_Cases', 'New_Cases']
                    colors = ['#1f77b4', '#ff7f0e']
                    
                    for metric, color in zip(metrics, colors):
                        fig_comparison.add_trace(go.Bar(
                            x=latest_data['Country/Region'],
                            y=latest_data[metric],
                            name=metric.replace('_', ' '),
                            marker_color=color,
                            text=latest_data[metric].apply(lambda x: f'{x:,}'),
                            textposition='auto'
                        ))
                    
                    fig_comparison.update_layout(
                        title='Country Comparison (Latest Data)',
                        barmode='group',
                        template='plotly_white',
                        xaxis_title='Country',
                        yaxis_title='Cases'
                    )
                    
                    st.plotly_chart(fig_comparison, use_container_width=True)
                else:
                    st.warning("No latest data available for comparison")
            
            # Heatmap of cases over time
            st.subheader("Heatmap of Cases Over Time")
            
            # Create pivot table for heatmap
            pivot_data = time_series_data.pivot_table(
                index='Country/Region',
                columns='Date',
                values='Total_Cases',
                aggfunc='sum'
            )
            
            if not pivot_data.empty:
                fig_heatmap = px.imshow(
                    pivot_data,
                    labels=dict(x="Date", y="Country", color="Total Cases"),
                    title="Cases Heatmap",
                    aspect="auto",
                    color_continuous_scale="Viridis"
                )
                
                st.plotly_chart(fig_heatmap, use_container_width=True)
            else:
                st.warning("Not enough data for heatmap visualization")
        else:
            st.warning("No data available for comparison")
    
    elif analysis_type == "Growth Analysis":
        st.header("📈 Growth Rate Analysis")
        
        if not time_series_data.empty:
            # Calculate daily growth rate with division by zero protection
            time_series_data['Daily_Growth_Rate'] = (
                time_series_data['New_Cases'] / 
                time_series_data['Total_Cases'].shift(1).replace(0, 1) * 100
            ).fillna(0)
            
            # Daily growth rate chart
            fig_growth = px.line(
                time_series_data,
                x='Date',
                y='Daily_Growth_Rate',
                color='Country/Region',
                title='Daily Growth Rate (%)',
                labels={'Daily_Growth_Rate': 'Growth Rate %', 'Date': 'Date'},
                template='plotly_white'
            )
            fig_growth.add_hline(y=0, line_dash="dash", line_color="gray")
            st.plotly_chart(fig_growth, use_container_width=True)
            
            # Weekly growth calculation
            st.subheader("Weekly Growth Analysis")
            
            # Create weekly summary
            time_series_data['Week_Start'] = time_series_data['Date'] - pd.to_timedelta(time_series_data['Date'].dt.dayofweek, unit='D')
            weekly_data = time_series_data.groupby(['Country/Region', 'Week_Start']).agg({
                'Total_Cases': 'last',
                'New_Cases': 'sum'
            }).reset_index()
            
            # Calculate weekly growth with division by zero protection
            weekly_data['Weekly_Growth'] = weekly_data.groupby('Country/Region')['Total_Cases'].pct_change(fill_method=None) * 100
            weekly_data['Weekly_Growth'] = weekly_data['Weekly_Growth'].fillna(0)
            
            fig_weekly = px.line(
                weekly_data,
                x='Week_Start',
                y='Weekly_Growth',
                color='Country/Region',
                title='Weekly Growth Rate (%)',
                labels={'Weekly_Growth': 'Weekly Growth %', 'Week_Start': 'Week Starting'},
                template='plotly_white'
            )
            st.plotly_chart(fig_weekly, use_container_width=True)
            
            # Show growth statistics
            st.subheader("Growth Statistics")
            
            for country in selected_countries[:3]:  # Limit to first 3 for readability
                country_data = time_series_data[time_series_data['Country/Region'] == country]
                if not country_data.empty and len(country_data) > 0:
                    avg_growth = country_data['Daily_Growth_Rate'].mean()
                    max_growth = country_data['Daily_Growth_Rate'].max()
                    recent_growth = country_data['Daily_Growth_Rate'].iloc[-1]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(f"{country} Avg Growth", f"{avg_growth:.2f}%")
                    with col2:
                        st.metric(f"{country} Peak Growth", f"{max_growth:.2f}%")
                    with col3:
                        st.metric(f"{country} Recent Growth", f"{recent_growth:.2f}%")
        else:
            st.warning("No data available for growth analysis")
    
    # =================== DATA DOWNLOAD ===================
    if not time_series_data.empty:
        st.markdown("---")
        st.subheader("💾 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Download time series data
            csv_time_series = time_series_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Time Series Data (CSV)",
                data=csv_time_series,
                file_name="covid_time_series_data.csv",
                mime="text/csv",
            )
        
        with col2:
            # Download summary statistics
            if 'summary_stats' in locals() and 'summary_stats' in globals():
                summary_stats = get_summary_statistics(time_series_data)
                if not summary_stats.empty:
                    csv_summary = summary_stats.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Summary Statistics (CSV)",
                        data=csv_summary,
                        file_name="covid_summary_statistics.csv",
                        mime="text/csv",
                    )

# Information panel
st.markdown("---")
st.success("""
✅ **Enhanced Dashboard Features Added:**
1. **Time Series Transformation** - Converted wide data to analyzable long format
2. **Multiple Analysis Views** - Time series, summary stats, comparisons, growth analysis
3. **Interactive Visualizations** - Line charts, bar charts, heatmaps
4. **Date Range Filtering** - Analyze specific time periods
5. **Data Export** - Download processed data for further analysis
""")

# Footer
st.markdown("---")
st.caption("© 2023 | Created by Juliet Oni | Data Analyst Portfolio Project")