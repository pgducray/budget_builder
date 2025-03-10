"""
Streamlit application for budget analysis and categorization.
"""
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from pathlib import Path
from src.gui.categorization_page import render_categorization_page
from src.database.categories import CategoryManager
from src.database.rules import RuleManager
from src.database.transactions import TransactionManager


def load_data():
    conn = sqlite3.connect('data/transactions.db')

    # Load transactions with category names
    transactions = pd.read_sql('''
        SELECT
            t.date,
            t.description,
            t.amount,
            c.name as category,
            r.pattern as rule_pattern
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN categorization_rules r ON t.rule_id = r.id
    ''', conn)

    # Convert date to datetime
    transactions['date'] = pd.to_datetime(transactions['date'])

    conn.close()
    return transactions


def create_monthly_chart(df, height):
    monthly_category_spending = df.groupby([
        df['date'].dt.strftime('%Y-%m'),
        'category'
    ])['amount'].sum().reset_index()

    fig = px.bar(
        monthly_category_spending,
        x='date',
        y='amount',
        color='category',
        title='Monthly Spending by Category',
        labels={'date': 'Month', 'amount': 'Total Amount ($)', 'category': 'Category'},
        height=height,
        template="plotly_white",
        barmode='stack'
    )

    # Customize hover data
    fig.update_traces(
        hovertemplate="<br>".join([
            "Month: %{x}",
            "Category: %{customdata[0]}",
            "Amount: $%{y:,.2f}",
            "<extra></extra>"
        ]),
        customdata=monthly_category_spending[['category']]
    )

    # Improve layout
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=60)
    )

    return fig


def create_category_chart(df, height):
    category_spending = df.groupby('category').agg({
        'amount': 'sum',
        'description': 'count'
    }).reset_index()
    category_spending['avg_transaction'] = category_spending['amount'] / category_spending['description']

    fig = px.bar(
        category_spending,
        y='category',
        x='amount',
        title='Spending by Category',
        orientation='h',
        labels={'category': 'Category', 'amount': 'Total Amount ($)'},
        height=height,
        template="plotly_white",
        color='avg_transaction',
        color_continuous_scale='Viridis',
        custom_data=['description', 'avg_transaction']
    )

    # Customize hover data
    fig.update_traces(
        hovertemplate="<br>".join([
            "Category: %{y}",
            "Total Amount: $%{x:,.2f}",
            "Transaction Count: %{customdata[0]:,}",
            "Avg Transaction: $%{customdata[1]:.2f}",
            "<extra></extra>"
        ])
    )

    # Improve layout
    fig.update_layout(
        coloraxis_colorbar_title="Avg Transaction ($)",
        margin=dict(t=60, r=120)
    )

    return fig


def create_rules_chart(df, height):
    rule_usage = df[df['rule_pattern'].notna()].groupby('rule_pattern').agg({
        'amount': ['sum', 'mean'],
        'description': 'count'
    }).reset_index()
    rule_usage.columns = ['rule', 'total_amount', 'avg_amount', 'count']

    fig = px.bar(
        rule_usage,
        y='rule',
        x='count',
        title='Rule Usage Analysis',
        orientation='h',
        labels={'rule': 'Rule Pattern', 'count': 'Number of Transactions'},
        height=height,
        template="plotly_white",
        color='avg_amount',
        color_continuous_scale='Viridis',
        custom_data=['total_amount', 'avg_amount']
    )

    # Customize hover data
    fig.update_traces(
        hovertemplate="<br>".join([
            "Rule: %{y}",
            "Transactions: %{x:,}",
            "Total Amount: $%{customdata[0]:,.2f}",
            "Avg Amount: $%{customdata[1]:.2f}",
            "<extra></extra>"
        ])
    )

    # Improve layout
    fig.update_layout(
        coloraxis_colorbar_title="Avg Amount ($)",
        margin=dict(t=60, r=120)
    )

    return fig


def main():
    st.set_page_config(layout="wide")  # Use wide layout

    # Initialize database managers
    # Ensure data directory exists
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)

    # Initialize database path
    db_path = data_dir / 'transactions.db'
    category_manager = CategoryManager(db_path)
    rule_manager = RuleManager(db_path)
    transaction_manager = TransactionManager(db_path)

    # Initialize database if needed
    category_manager.initialize_database()

    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Categorization"],
        index=0
    )

    if page == "Dashboard":
        # Load data
        df = load_data()

        # Sidebar filters
        st.sidebar.title('Filters')

        # Year and Month filters
        years = sorted(df['date'].dt.year.unique())
        months = list(range(1, 13))
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']

        selected_years = st.sidebar.multiselect(
            'Select Years',
            options=years,
            default=years
        )

        selected_months = st.sidebar.multiselect(
            'Select Months',
            options=list(range(1, 13)),
            default=list(range(1, 13)),
            format_func=lambda x: month_names[x-1]
        )

        # Category filter
        st.sidebar.subheader('Categories')
        categories = [cat for cat in df['category'].unique() if cat is not None]
        categories.sort()  # Sort in place
        selected_categories = st.sidebar.multiselect(
            'Select Categories',
            options=categories,
            default=categories
        )

        # Rule filter
        st.sidebar.subheader('Rules')
        rules = [rule for rule in df['rule_pattern'].unique() if rule is not None]
        rules.sort()  # Sort in place
        selected_rules = st.sidebar.multiselect(
            'Select Rules',
            options=rules,
            default=rules
        )

        # Zoom control
        zoom_factor = st.sidebar.slider(
            'Chart Height (%)',
            min_value=50,
            max_value=150,
            value=100,
            step=10
        )
        base_height = 200  # Base height for charts
        chart_height = int(base_height * zoom_factor / 100)

        # Apply filters
        filtered_df = df.copy()
        filtered_df = filtered_df[
            (filtered_df['date'].dt.year.isin(selected_years)) &
            (filtered_df['date'].dt.month.isin(selected_months)) &
            (
                filtered_df['category'].isin(selected_categories) |
                filtered_df['category'].isna()  # Include uncategorized transactions
            )
        ]
        if selected_rules:
            filtered_df = filtered_df[
                filtered_df['rule_pattern'].isin(selected_rules) |
                filtered_df['rule_pattern'].isna()
            ]

        # Main content
        st.title('Budget Analysis Dashboard')

        # Summary metrics
        total_amount = filtered_df['amount'].sum()
        transaction_count = len(filtered_df)
        avg_transaction = total_amount / transaction_count if transaction_count > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Amount", f"${total_amount:,.2f}")
        col2.metric("Transaction Count", f"{transaction_count:,}")
        col3.metric("Average Transaction", f"${avg_transaction:,.2f}")

        # 1. Monthly spending chart (full width)
        st.plotly_chart(
            create_monthly_chart(filtered_df, chart_height),
            use_container_width=True
        )

        # Create two columns for category and rules charts
        viz_col1, viz_col2 = st.columns(2)

        # 2. Category spending chart (left column)
        with viz_col1:
            st.plotly_chart(
                create_category_chart(filtered_df, chart_height),
                use_container_width=True
            )

        # 3. Rules analysis chart (right column)
        with viz_col2:
            st.plotly_chart(
                create_rules_chart(filtered_df, chart_height),
                use_container_width=True
            )

        # 4. Transactions table
        st.subheader('Transactions')
        st.dataframe(
            filtered_df[['date', 'description', 'amount', 'category', 'rule_pattern']]
            .sort_values('date', ascending=False),
            use_container_width=True,
            height=250  # Fixed height for table
        )

    else:  # Categorization page
        render_categorization_page(transaction_manager, category_manager, rule_manager)


if __name__ == '__main__':
    main()
