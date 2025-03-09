import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import altair as alt

# Add parent directory to path to import from sibling packages
sys.path.append(str(Path(__file__).parent.parent))

from analytics.spending import SpendingAnalyzer
from analytics.budget import BudgetAnalyzer
from database.transactions import TransactionManager
from database.rules import RuleManager

def filter_transactions(transactions, start_date, end_date, category, selected_month=None):
    """Filter transactions based on date range, category, and selected month"""
    filtered = transactions.copy()
    filtered['Date'] = pd.to_datetime(filtered['Date'])

    # Apply date range filter
    if start_date and end_date:
        filtered = filtered[
            (filtered['Date'].dt.date >= start_date) &
            (filtered['Date'].dt.date <= end_date)
        ]

    # Apply month filter if selected
    if selected_month:
        filtered = filtered[filtered['Date'].dt.strftime('%Y-%m') == selected_month]

    # Apply category filter
    if category and category != "All Categories":
        filtered = filtered[filtered['Category'] == category]

    return filtered

def main():
    # Initialize session state for transaction details
    if 'show_transaction_details' not in st.session_state:
        st.session_state.show_transaction_details = False
        st.session_state.selected_transaction = None
    st.set_page_config(
        page_title="Budget Builder",
        page_icon="💰",
        layout="wide"
    )

    st.title("Budget Builder Dashboard")

    # Sidebar for filters
    st.sidebar.header("Filters")

    # Date range filter with defaults
    default_start = pd.Timestamp('2024-01-01').date()
    default_end = pd.Timestamp('2024-12-31').date()
    start_date = st.sidebar.date_input("Start Date", default_start)
    end_date = st.sidebar.date_input("End Date", default_end)

    # Category filter
    categories = ["All Categories", "Food", "Transport", "Shopping", "Bills"]
    selected_category = st.sidebar.selectbox("Category", categories)

    # Main sections
    tab1, tab2, tab3 = st.tabs(["Monthly Analysis", "Category Analysis", "Rules Management"])

    with tab1:
        st.header("Monthly Spending Analysis")

        # Sample monthly data
        monthly_data = pd.DataFrame({
            'Month': ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
            'Spending': [1200, 1500, 1100, 1600, 1300, 1400]
        })

        # Monthly trend chart
        monthly_chart = alt.Chart(monthly_data).mark_line(point=True).encode(
            x=alt.X('Month:O', title='Month'),
            y=alt.Y('Spending:Q', title='Total Spending'),
            tooltip=['Month', 'Spending']
        ).properties(
            width=600,
            height=400,
            title='Monthly Spending Trend'
        )

        st.altair_chart(monthly_chart)

        # Month selector
        selected_month = st.selectbox(
            "Select Month for Details",
            options=monthly_data['Month'].tolist(),
            format_func=lambda x: pd.to_datetime(x).strftime('%B %Y')
        )

        # Sample transactions data with rules
        transactions = pd.DataFrame({
            'Date': [
                '2024-01-15', '2024-01-20', '2024-02-01',
                '2024-02-15', '2024-03-01', '2024-03-15'
            ],
            'Description': [
                'Grocery Store', 'Gas Station', 'Restaurant',
                'Shopping Mall', 'Utility Bill', 'Internet Bill'
            ],
            'Amount': [120.50, 45.00, 35.75, 200.00, 150.00, 80.00],
            'Category': ['Food', 'Transport', 'Food', 'Shopping', 'Bills', 'Bills'],
            'Applied Rule': [
                'Rule 1: *Grocery*', 'Rule 2: *Gas*', 'Rule 1: *Restaurant*',
                'Rule 2: *Mall*', 'Rule 1: *Utility*', 'Rule 2: *Internet*'
            ]
        })

        # Apply filters including selected month
        filtered_transactions = filter_transactions(
            transactions,
            start_date,
            end_date,
            selected_category,
            selected_month
        )

        # Show number of transactions
        st.subheader(f"Transactions ({len(filtered_transactions)} items)")

        # Display transactions with view buttons
        st.dataframe(filtered_transactions, use_container_width=True)

        # Add view buttons for each transaction
        for idx, row in filtered_transactions.iterrows():
            if st.button(f"View Details #{idx + 1}", key=f"btn_{idx}"):
                with st.expander("Transaction Details", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("Date:", row['Date'])
                        st.write("Description:", row['Description'])
                    with col2:
                        st.write("Amount:", row['Amount'])
                        st.write("Category:", row['Category'])
                        st.write("Rule Applied:", row['Applied Rule'])

    with tab2:
        st.header("Category Analysis")

        # Calculate category totals
        if len(filtered_transactions) > 0:
            category_totals = filtered_transactions.groupby('Category')['Amount'].sum().reset_index()

            # Category distribution chart
            pie = alt.Chart(category_totals).mark_arc().encode(
                theta=alt.Theta(field='Amount', type='quantitative'),
                color=alt.Color(field='Category', type='nominal'),
                tooltip=[
                    alt.Tooltip('Category:N'),
                    alt.Tooltip('Amount:Q', format='$.2f')
                ]
            ).properties(
                width=400,
                height=400,
                title='Spending by Category'
            )
            st.altair_chart(pie)
        else:
            st.info("No transactions found for the selected filters")

        # Show transactions for selected category
        st.subheader(f"Transactions ({len(filtered_transactions)} items)")
        if len(filtered_transactions) > 0:
            st.dataframe(filtered_transactions, use_container_width=True)
        else:
            st.info("No transactions match the current filters")

        # Add view buttons for each transaction
        for idx, row in filtered_transactions.iterrows():
            if st.button(f"View Details #{idx + 1}", key=f"cat_btn_{idx}"):
                with st.expander("Transaction Details", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("Date:", row['Date'])
                        st.write("Description:", row['Description'])
                    with col2:
                        st.write("Amount:", row['Amount'])
                        st.write("Category:", row['Category'])

    with tab3:
        st.header("Rules Management")

        # Add new rule section
        with st.expander("Add New Rule", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                new_pattern = st.text_input("Pattern")
                new_category = st.selectbox("Category", categories[1:])  # Exclude "All Categories"
            with col2:
                st.write("Rule Preview")
                if new_pattern and new_category:
                    st.info(f"Match '{new_pattern}' → Categorize as '{new_category}'")
            if st.button("Add Rule"):
                st.success("Rule added successfully!")

        # Existing rules table
        st.subheader("Existing Rules")
        rules_df = pd.DataFrame({
            "Rule": ["Rule 1", "Rule 2"],
            "Pattern": ["pattern1", "pattern2"],
            "Category": ["cat1", "cat2"],
            "Matches": [10, 5]  # Number of transactions matched
        })

        # Rules table with view transactions button
        for idx, rule in rules_df.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{rule['Rule']}**: Match '{rule['Pattern']}' → {rule['Category']}")
            with col2:
                st.write(f"{rule['Matches']} matches")
            with col3:
                if st.button("View Transactions", key=f"rule_trans_{idx}"):
                    # Filter transactions that use this rule
                    rule_transactions = transactions[
                        transactions['Applied Rule'].str.startswith(rule['Rule'])
                    ]
                    with st.expander(f"Transactions using {rule['Rule']}", expanded=True):
                        st.dataframe(rule_transactions, use_container_width=True)

        # Add edit button for rules
        if st.button("Edit Rules"):
            edited_rules = st.data_editor(
                rules_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Matches": st.column_config.NumberColumn(
                        help="Number of transactions matched by this rule"
                    ),
                    "Category": st.column_config.SelectboxColumn(options=categories[1:])
                }
            )

if __name__ == "__main__":
    main()
