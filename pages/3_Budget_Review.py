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

def calculate_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate monthly income, expenses, and savings."""
    # Convert transaction_date to datetime
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], format='%d/%m/%Y')

    # Create month and year columns
    df['month_year'] = df['transaction_date'].dt.strftime('%Y-%m')

    # Calculate monthly totals
    monthly = df.groupby('month_year').agg(
        income=('amount', lambda x: x[x > 0].sum()),
        expenses=('amount', lambda x: abs(x[x < 0].sum())),
        net_savings=('amount', 'sum')
    ).reset_index()

    return monthly.sort_values('month_year')

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

def plot_monthly_trends(monthly_data: pd.DataFrame):
    """Plot monthly income, expenses, and savings trends."""
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
        line=dict(color='green')
    ))

    fig.add_trace(go.Scatter(
        x=monthly_data['month_year'],
        y=monthly_data['expenses'],
        name='Expenses',
        line=dict(color='red')
    ))

    fig.add_trace(go.Scatter(
        x=monthly_data['month_year'],
        y=monthly_data['net_savings'],
        name='Net Savings',
        line=dict(color='blue')
    ))

    fig.update_layout(
        title='Monthly Financial Trends',
        xaxis_title='Month',
        yaxis_title='Amount (Rs)',
        **CHART_CONFIG['line']['layout']
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_category_impact(df: pd.DataFrame, month_year: str):
    """Plot category-wise spending for a specific month."""
    # Filter data for the selected month
    month_data = df[
        df['transaction_date'].dt.strftime('%Y-%m') == month_year
    ]

    # Calculate category totals (expenses only)
    category_totals = month_data[month_data['amount'] < 0].groupby('Category').agg({
        'amount': 'sum'
    }).reset_index()

    # Sort by absolute amount
    category_totals['amount'] = category_totals['amount'].abs()
    category_totals = category_totals.sort_values('amount', ascending=True)

    # Create horizontal bar chart
    # Create horizontal bar chart
    fig = go.Figure(go.Bar(
        x=category_totals['amount'],
        y=category_totals['Category'],
        orientation='h'
    ))

    # Update layout with both custom and config settings
    layout = {
        'title': f'Category-wise Spending for {month_year}'
    }
    layout.update(CHART_CONFIG['bar']['layout'])
    fig.update_layout(**layout)

    st.plotly_chart(fig, use_container_width=True)

def display_transactions_table(df: pd.DataFrame, month_year: str, category: str = None):
    """Display transactions for selected month and category."""
    # Filter by month
    mask = df['transaction_date'].dt.strftime('%Y-%m') == month_year

    # Additional category filter if specified
    if category:
        mask &= df['Category'] == category

    # Get filtered transactions
    transactions = df[mask].sort_values('transaction_date', ascending=False)

    if not transactions.empty:
        st.dataframe(
            transactions[DISPLAY_CONFIG['transactions_columns']],
            use_container_width=True
        )
    else:
        st.info("No transactions found for the selected criteria.")

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

    # Calculate monthly summary
    monthly_summary = calculate_monthly_summary(df)

    # Display monthly metrics
    st.subheader("Monthly Overview")
    display_monthly_metrics(monthly_summary)

    # Plot monthly trends
    plot_monthly_trends(monthly_summary)

    # Add month selector
    available_months = sorted(monthly_summary['month_year'].unique(), reverse=True)
    selected_month = st.selectbox(
        "Select Month for Detailed Analysis",
        available_months
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
        st.subheader(f"All Transactions for {selected_month}")
        display_transactions_table(df, selected_month)

if __name__ == "__main__":
    main()
