"""
Transaction analysis page.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.utils import (
    load_data, load_categorizer, get_frequent_transactions,
    check_pattern_updates, init_session_state
)
from src.analysis import (
    group_uncategorized, analyze_pattern_effectiveness
)

# Initialize session state
init_session_state()

st.set_page_config(page_title="Transaction Analysis", layout="wide")

def display_filters(df):
    """Display and apply transaction filters."""
    col1, col2 = st.columns(2)

    with col1:
        categories = ['All'] + sorted(df['Category'].unique().tolist())
        selected_category = st.selectbox("Filter by Category", categories)

    with col2:
        search = st.text_input("Search Descriptions", "")

    # Apply filters
    filtered_df = df.copy()
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['Category'] == selected_category]
    if search:
        filtered_df = filtered_df[filtered_df['description'].str.contains(search, case=False)]

    return filtered_df, selected_category

def display_category_stats(df):
    """Display category statistics and charts."""
    total = len(df)
    uncategorized = len(df[df['Category'] == 'Uncategorized'])

    # Statistics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Transactions", total)
        st.metric("Categorized", f"{((total - uncategorized)/total)*100:.1f}%")
        st.metric("Uncategorized", uncategorized)

    with col2:
        # Category distribution
        category_counts = df['Category'].value_counts()
        fig = px.pie(
            values=category_counts.values,
            names=category_counts.index,
            title="Transaction Distribution by Category"
        )
        st.plotly_chart(fig, use_container_width=True)

def display_frequency_analysis(df, category):
    """Display transaction frequency analysis."""
    st.subheader(f"Most Frequent Transactions {f'in {category}' if category != 'All' else ''}")

    frequent = get_frequent_transactions(df, category)

    # Create bar chart
    fig = go.Figure([
        go.Bar(name='Count', x=frequent.index, y=frequent['Count']),
        go.Bar(name='Total Amount', x=frequent.index, y=frequent['Total Amount'])
    ])

    fig.update_layout(
        barmode='group',
        title="Transaction Frequency and Amounts",
        xaxis_title="Transaction Description",
        yaxis_title="Count / Amount",
        xaxis_tickangle=-45
    )

    st.plotly_chart(fig, use_container_width=True)

    # Show detailed table
    st.dataframe(frequent, use_container_width=True)

def load_and_categorize():
    """Load data and categorize transactions."""
    df = load_data()
    if df is None:
        st.error("No transaction data found. Please run process_statements.py first.")
        return None, None

    categorizer = load_categorizer()
    df = categorizer.categorize_transactions(df)
    return df, categorizer

def main():
    """Main analysis page."""
    st.title("Transaction Analysis")

    # Check for pattern updates
    if check_pattern_updates() or st.session_state.data is None:
        df, categorizer = load_and_categorize()
        if df is None:
            return
        st.session_state.data = df
        st.session_state.categorizer = categorizer
    else:
        df = st.session_state.data
        categorizer = st.session_state.categorizer

    # Add manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        # Force full re-categorization
        df = load_data()
        categorizer = load_categorizer()
        df = categorizer.categorize_transactions(df)
        st.session_state.data = df
        # Reset pattern matches cache
        st.session_state.pattern_matches = {}
        st.success("Data refreshed with latest patterns!")
        st.rerun()

    # Display filters and get filtered data
    filtered_df, selected_category = display_filters(df)

    # Main content
    tab1, tab2, tab3 = st.tabs(["Transactions", "Analysis", "Pattern Effectiveness"])

    with tab1:
        st.dataframe(
            filtered_df[['description', 'amount', 'Category', 'Matching Pattern']],
            use_container_width=True
        )

    with tab2:
        display_category_stats(filtered_df)
        display_frequency_analysis(filtered_df, selected_category)

    with tab3:
        st.subheader("Pattern Effectiveness")

        # Show effectiveness metrics for each pattern
        for pattern, category in categorizer.patterns.items():
            with st.expander(f"Pattern: {pattern} ({category})"):
                metrics = analyze_pattern_effectiveness(pattern, df)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Matching Transactions", metrics['matching_transactions'])
                with col2:
                    st.metric("Unique Descriptions", metrics['unique_descriptions'])
                with col3:
                    st.metric(
                        "Impact on Uncategorized",
                        f"{metrics['impact_on_uncategorized']*100:.1f}%"
                    )

                st.write("Sample Matches:")
                st.write(", ".join(metrics['sample_matches']))

    # Export option
    if st.sidebar.button("Export Categorized Transactions"):
        output_path = Path("data/categorized_transactions.csv")
        df.to_csv(output_path, index=False)
        st.sidebar.success(f"Exported to {output_path}")

if __name__ == "__main__":
    main()
