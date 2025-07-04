"""
Budget review page for analyzing spending patterns and savings.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from pathlib import Path
from src.utils import init_session_state
from src.config import CHART_CONFIG, DISPLAY_CONFIG
from src.shared.components import (
    create_page_config, display_data_error,
    load_app_data, TransactionAnalyzer
)

# Initialize session state
init_session_state()

# Set up page
create_page_config("Budget Review")

def format_amount_k(amount):
    """Format amount in thousands with K suffix."""
    return f"{amount/1000:.1f}K" if abs(amount) >= 1000 else f"{amount:.1f}"

def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess dataframe with common transformations."""
    if 'transaction_date' not in df.columns or not isinstance(df['transaction_date'].iloc[0], pd.Timestamp):
        df = df.copy()
        df['transaction_date'] = pd.to_datetime(df['transaction_date'], format='%d/%m/%Y')
        df['month_year'] = df['transaction_date'].dt.strftime('%Y-%m')
    return df

def get_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Get cached monthly summary or calculate if not available."""
    if 'monthly_summary' not in st.session_state:
        df = preprocess_dataframe(df)
        monthly = df.groupby('month_year').agg(
            income=('amount', lambda x: x[x > 0].sum()),
            expenses=('amount', lambda x: abs(x[x < 0].sum())),
            net_savings=('amount', 'sum')
        ).reset_index()
        st.session_state.monthly_summary = monthly.sort_values('month_year')
    return st.session_state.monthly_summary

def display_monthly_metrics(monthly_data: pd.DataFrame):
    """Display key monthly metrics."""
    if not monthly_data.empty:
        latest = monthly_data.iloc[-1]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Monthly Income",
                f"Rs {latest['income']:,.2f}",
                delta=f"{((latest['income'] - monthly_data.iloc[-2]['income']) / monthly_data.iloc[-2]['income'] * 100):.1f}%"
            )

        with col2:
            st.metric(
                "Monthly Expenses",
                f"Rs {latest['expenses']:,.2f}",
                delta=f"{((latest['expenses'] - monthly_data.iloc[-2]['expenses']) / monthly_data.iloc[-2]['expenses'] * 100):.1f}%",
                delta_color="inverse"
            )

        with col3:
            st.metric(
                "Net Savings",
                f"Rs {latest['net_savings']:,.2f}",
                delta=f"{((latest['net_savings'] - monthly_data.iloc[-2]['net_savings']) / abs(monthly_data.iloc[-2]['net_savings']) * 100):.1f}%"
            )

def plot_monthly_trends(df: pd.DataFrame):
    """Plot monthly income, expenses, and savings trends."""
    monthly_data = get_monthly_summary(df)

    fig = go.Figure()

    # Add colored background shapes for savings/losses visualization
    fig.add_shape(
        type="rect",
        x0=monthly_data['month_year'].iloc[0],
        x1=monthly_data['month_year'].iloc[-1],
        y0=0,
        y1=monthly_data['net_savings'].max() * 1.1,  # Add 10% padding
        fillcolor="rgba(0,255,0,0.1)",  # Light green
        line_width=0,
        layer="below"
    )

    fig.add_shape(
        type="rect",
        x0=monthly_data['month_year'].iloc[0],
        x1=monthly_data['month_year'].iloc[-1],
        y0=monthly_data['net_savings'].min() * 1.1,  # Add 10% padding
        y1=0,
        fillcolor="rgba(255,0,0,0.1)",  # Light red
        line_width=0,
        layer="below"
    )

    # Add zero line
    fig.add_hline(
        y=0,
        line_dash="solid",
        line_color="gray",
        line_width=1
    )

    # Add traces for income, expenses, and savings
    fig.add_trace(go.Scatter(
        x=monthly_data['month_year'],
        y=monthly_data['income'],
        name='Income',
        line=dict(color='green'),
        hovertemplate="Income: %{y:,.1f}K<br>%{x}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=monthly_data['month_year'],
        y=monthly_data['expenses'],
        name='Expenses',
        line=dict(color='red'),
        hovertemplate="Expenses: %{y:,.1f}K<br>%{x}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=monthly_data['month_year'],
        y=monthly_data['net_savings'],
        name='Net Savings',
        line=dict(color='blue'),
        hovertemplate="Net Savings: %{y:,.1f}K<br>%{x}<extra></extra>"
    ))

    setup_graph_layout(fig, 'Monthly Financial Trends')

    st.plotly_chart(fig, use_container_width=True)

def get_monthly_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Get cached monthly category summary or calculate if not available."""
    if 'monthly_category_summary' not in st.session_state:
        df = preprocess_dataframe(df)
        monthly_category = df.groupby(['month_year', 'Category'])['amount'].sum().reset_index()
        st.session_state.monthly_category_summary = monthly_category.sort_values(['month_year', 'Category'])
    return st.session_state.monthly_category_summary

def setup_graph_layout(fig: go.Figure, title: str):
    """Apply common graph layout settings."""
    # First apply config settings
    fig.update_layout(**CHART_CONFIG['line']['layout'])

    # Then override/add specific settings
    fig.update_layout(
        title=title,
        xaxis_title='Month',
        yaxis_title='Amount (Rs)',
        yaxis=dict(
            tickformat=".1f",
            ticksuffix="K"
        )
    )

def plot_monthly_category_trends(df: pd.DataFrame):
    """Plot monthly trends by category."""
    monthly_category_data = get_monthly_category_summary(df)

    # Get unique categories for selection
    categories = sorted(df['Category'].unique())

    # Move category selection to sidebar
    with st.sidebar:
        st.subheader("Category Filters")
        selected_categories = st.multiselect(
            "Select Categories to Display",
            categories,
            default=categories[:5]  # Default to first 5 categories
        )

        # Store selection in session state for reuse
        st.session_state.selected_categories = selected_categories

    if not selected_categories:
        st.warning("Please select at least one category to display the trends.")
        return

    fig = go.Figure()

    # Plot selected categories
    for category in selected_categories:
        category_data = monthly_category_data[monthly_category_data['Category'] == category]
        fig.add_trace(go.Scatter(
            x=category_data['month_year'],
            y=category_data['amount'],
            name=category,
            hovertemplate=f"{category}: %{{y:,.1f}}K<br>%{{x}}<extra></extra>"
        ))

    setup_graph_layout(fig, 'Monthly Category Trends')

    st.plotly_chart(fig, use_container_width=True)

def plot_category_impact(df: pd.DataFrame, month_year: str):
    """Plot category-wise spending for a specific month or all months."""
    df = preprocess_dataframe(df)

    # Filter data for the selected month or use all data
    if month_year == "All Months":
        month_data = df
        title_period = "All Time"
    else:
        month_data = df[df['month_year'] == month_year]
        title_period = month_year

    # Calculate category totals (all transactions)
    category_totals = month_data.groupby('Category')['amount'].sum().reset_index()
    category_totals = category_totals.sort_values('amount', ascending=True)

    # Create horizontal bar chart with colors based on amount
    fig = go.Figure(go.Bar(
        x=category_totals['amount'],
        y=category_totals['Category'],
        orientation='h',
        marker_color=['red' if x < 0 else 'green' for x in category_totals['amount']],
        text=[format_amount_k(x) for x in category_totals['amount']],
        textposition='outside'
    ))

    # First apply config settings
    fig.update_layout(**CHART_CONFIG['bar']['layout'])

    # Then override/add specific settings
    fig.update_layout(
        title=f'Category-wise Impact for {title_period} (Red: Expenses, Green: Income)',
        showlegend=False,
        xaxis=dict(
            tickformat=".1f",
            ticksuffix="K"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

def display_transactions_table(df: pd.DataFrame, month_year: str, category: str = None):
    """Display transactions for selected month and category."""
    df = preprocess_dataframe(df)

    # Initialize mask
    if month_year == "All Months":
        mask = pd.Series(True, index=df.index)
    else:
        mask = df['month_year'] == month_year

    # Use selected categories from session state if available
    if category and category != "All":
        mask &= df['Category'] == category
    elif st.session_state.get('selected_categories'):
        mask &= df['Category'].isin(st.session_state.selected_categories)

    # Get filtered transactions
    transactions = df[mask].sort_values('transaction_date', ascending=False)

    if not transactions.empty:
        st.dataframe(
            transactions[DISPLAY_CONFIG['transactions_columns']],
            use_container_width=True
        )
    else:
        st.info("No transactions found for the selected criteria.")

def clear_cache():
    """Clear all cached data to force fresh calculations."""
    # Clear data summaries
    if 'monthly_summary' in st.session_state:
        del st.session_state.monthly_summary
    if 'monthly_category_summary' in st.session_state:
        del st.session_state.monthly_category_summary

    # Clear data hash
    if 'data_hash' in st.session_state:
        del st.session_state.data_hash

    # Clear pattern matches
    if 'pattern_matches' in st.session_state:
        del st.session_state.pattern_matches

def main():
    """Main budget review page."""
    st.title("Budget Review")

    # Load data
    df, categorizer = load_app_data()
    if df is None:
        display_data_error()
        return

    # Create analyzer
    analyzer = TransactionAnalyzer(df)

    # Add manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        clear_cache()
        df, categorizer = load_app_data()
        st.success("Data refreshed! All views will update with latest categorizations.")
        st.rerun()

    # Initialize session state for data caching
    current_hash = hash(str(df))
    if st.session_state.get('data_hash') != current_hash:
        clear_cache()
        st.session_state.data_hash = current_hash

    # Calculate monthly summary
    monthly_summary = get_monthly_summary(df)

    # Display monthly metrics
    st.subheader("Monthly Overview")
    display_monthly_metrics(monthly_summary)

    # Plot monthly trends
    st.subheader("Overall Financial Trends")
    plot_monthly_trends(df)

    # Plot category trends
    st.subheader("Category-specific Trends")
    plot_monthly_category_trends(df)

    # Add month selector in sidebar
    with st.sidebar:
        st.markdown("---")
        st.subheader("Monthly Analysis")
        months = sorted(monthly_summary['month_year'].unique(), reverse=True)
        selected_month = st.selectbox(
            "Select Month for Analysis",
            ["All Months"] + months,
            help="Select 'All Months' to view data across all time periods"
        )

    # Create tabs for detailed analysis
    tab1, tab2 = st.tabs(["Category Impact", "Transactions"])

    with tab1:
        plot_category_impact(df, selected_month)

        # Add category selector for transactions
        categories = sorted(df['Category'].unique())
        selected_category = st.selectbox(
            "Select Category to View Transactions",
            ["All"] + categories
        )

        # Display transactions for selected category
        if selected_category == "All":
            display_transactions_table(df, selected_month)
        else:
            display_transactions_table(df, selected_month, selected_category)

    with tab2:
        period_text = "All Time" if selected_month == "All Months" else selected_month
        st.subheader(f"All Transactions for {period_text}")
        display_transactions_table(df, selected_month)

if __name__ == "__main__":
    main()
