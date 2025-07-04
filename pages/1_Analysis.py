"""
Transaction analysis page.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path
from src.utils import (
    get_frequent_transactions, init_session_state
)
from src.analysis import (
    group_uncategorized, analyze_pattern_effectiveness
)
from src.config import CHART_CONFIG, DISPLAY_CONFIG
from src.shared.components import (
    create_page_config, display_data_error,
    load_app_data, TransactionAnalyzer
)

# Initialize session state
init_session_state()

# Set up page
create_page_config("Transaction Analysis")

def display_filters(analyzer: TransactionAnalyzer):
    """Display and apply transaction filters."""
    col1, col2 = st.columns(2)

    with col1:
        categories = ['All'] + sorted(analyzer.df['Category'].unique().tolist())
        selected_category = st.selectbox("Filter by Category", categories)

    with col2:
        search = st.text_input("Search Descriptions", "")

    filtered_df = analyzer.get_filtered_data(selected_category, search)
    return filtered_df, selected_category

def display_category_stats(analyzer: TransactionAnalyzer, filtered_df: pd.DataFrame):
    """Display category statistics and charts."""
    stats = analyzer.get_category_stats()

    # Statistics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Transactions", stats['total'])
        st.metric("Categorized", f"{stats['categorized_pct']:.1f}%")
        st.metric("Uncategorized", stats['uncategorized'])

    with col2:
        # Category distribution
        category_counts = analyzer.get_category_distribution()
        fig = px.pie(
            values=category_counts.values,
            names=category_counts.index,
            **CHART_CONFIG['pie']['figure']
        )
        fig.update_layout(**CHART_CONFIG['pie']['layout'])
        st.plotly_chart(fig, use_container_width=True)

def display_frequency_analysis(df: pd.DataFrame, category: str):
    """Display transaction frequency analysis."""
    st.subheader(f"Most Frequent Transactions {f'in {category}' if category != 'All' else ''}")

    # Add limit slider
    limit = st.slider(
        "Number of transactions to show",
        min_value=5,
        max_value=50,
        value=DISPLAY_CONFIG['frequency_limit'],
        step=5
    )

    frequent = get_frequent_transactions(df, category, limit)

    # Create bar chart
    fig = go.Figure([
        go.Bar(name='Count', x=frequent.index, y=frequent['Count']),
        go.Bar(name='Total Amount', x=frequent.index, y=frequent['Total Amount'])
    ])

    fig.update_layout(**CHART_CONFIG['bar']['figure'])
    st.plotly_chart(fig, use_container_width=True)

    # Show detailed table
    st.dataframe(frequent, use_container_width=True)

def main():
    """Main analysis page."""
    st.title("Transaction Analysis")

    # Load data
    df, categorizer = load_app_data()
    if df is None:
        display_data_error()
        return

    # Create analyzer
    analyzer = TransactionAnalyzer(df)

    # Add manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        df, categorizer = load_app_data()
        st.session_state.pattern_matches = {}
        st.success("Data refreshed with latest patterns!")
        st.rerun()

    # Display filters and get filtered data
    filtered_df, selected_category = display_filters(analyzer)

    # Main content
    tab1, tab2, tab3 = st.tabs(["Transactions", "Analysis", "Pattern Effectiveness"])

    with tab1:
        st.dataframe(
            filtered_df[DISPLAY_CONFIG['transactions_columns']],
            use_container_width=True
        )

    with tab2:
        display_category_stats(analyzer, filtered_df)
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
