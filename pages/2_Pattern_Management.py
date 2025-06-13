"""
Pattern management page.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from src.utils import (
    load_data, load_categorizer, save_patterns,
    get_categories, update_pattern_timestamp,
    init_session_state, update_pattern_matches
)
from src.analysis import (
    group_uncategorized, suggest_pattern,
    analyze_pattern_effectiveness
)

# Initialize session state
init_session_state()

st.set_page_config(page_title="Pattern Management", layout="wide")

def display_pattern_preview(df: pd.DataFrame, pattern: str, category: str):
    """Display preview of transactions that would match a new pattern."""
    import re
    matches = df[df['description'].str.contains(pattern, case=False, regex=True)]
    if not matches.empty:
        st.write(f"Preview: {len(matches)} matching transactions found")
        st.dataframe(
            matches[['description', 'amount', 'Category']].head(),
            use_container_width=True
        )
    else:
        st.warning("No matching transactions found")

def edit_pattern(df: pd.DataFrame, pattern: str, category: str, categorizer):
    """Edit an existing pattern."""
    st.session_state.editing_pattern = pattern
    st.session_state.editing_category = category

    # Pattern input
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        new_pattern = st.text_input("Edit Pattern", value=pattern)
    with col2:
        new_category = st.selectbox(
            "Select Category",
            get_categories(),
            index=get_categories().index(category)
        )
    with col3:
        if st.button("View Matches"):
            st.session_state.preview_pattern = new_pattern
            st.session_state.preview_category = new_category

    # Show preview if requested
    if st.session_state.preview_pattern == new_pattern:
        with st.expander("Pattern Matches", expanded=True):
            display_pattern_preview(df, new_pattern, new_category)

    # Save/Cancel buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Changes"):
            if pattern != new_pattern or category != new_category:
                # Update patterns
                categorizer.remove_pattern(pattern)
                categorizer.add_pattern(new_pattern, new_category)
                save_patterns(categorizer)

                st.success("Pattern saved! Refresh Analysis page to see changes.")
                st.session_state.editing_pattern = None
                st.session_state.preview_pattern = None
                st.rerun()
    with col2:
        if st.button("Cancel"):
            st.session_state.editing_pattern = None
            st.session_state.preview_pattern = None
            st.rerun()

def manage_patterns(df: pd.DataFrame, categorizer):
    """Pattern management interface with live preview."""
    st.subheader("Current Patterns")

    # Calculate match counts only if needed
    if not st.session_state.pattern_matches:
        for pattern, category in categorizer.patterns.items():
            match_count = len(df[df['description'].str.contains(pattern, case=False, regex=True)])
            st.session_state.pattern_matches[pattern] = match_count

    # Display patterns using cached counts
    patterns_data = [
        {
            'Pattern': pattern,
            'Category': category,
            'Matching Transactions': st.session_state.pattern_matches.get(pattern, 0)
        }
        for pattern, category in categorizer.patterns.items()
    ]

    patterns_df = pd.DataFrame(patterns_data)

    # Display patterns with edit buttons
    for idx, row in patterns_df.iterrows():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            st.text(row['Pattern'])
        with col2:
            st.text(row['Category'])
        with col3:
            st.text(f"{row['Matching Transactions']} matches")
        with col4:
            if st.button("Edit", key=f"edit_{idx}"):
                st.session_state.editing_pattern = row['Pattern']
                st.session_state.editing_category = row['Category']

    # Show edit form if a pattern is being edited
    if st.session_state.editing_pattern:
        st.markdown("---")
        edit_pattern(
            df,
            st.session_state.editing_pattern,
            st.session_state.editing_category,
            categorizer
        )

    # Add new pattern
    st.markdown("---")
    st.subheader("Add New Pattern")

    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        new_pattern = st.text_input("Regex Pattern")
    with col2:
        new_category = st.selectbox("Select Category", get_categories())
    with col3:
        if st.button("View Matches", key="preview_new"):
            st.session_state.preview_pattern = new_pattern
            st.session_state.preview_category = new_category

    # Show preview if requested
    if st.session_state.preview_pattern == new_pattern:
        with st.expander("Pattern Matches", expanded=True):
            display_pattern_preview(df, new_pattern, new_category)

    if st.button("Add Pattern") and new_pattern:
        # Calculate matches for new pattern only
        match_count = len(df[df['description'].str.contains(new_pattern, case=False, regex=True)])
        st.session_state.pattern_matches[new_pattern] = match_count

        categorizer.add_pattern(new_pattern, new_category)
        save_patterns(categorizer)
        st.success("Pattern saved! Refresh Analysis page to see changes.")
        st.session_state.preview_pattern = None
        st.rerun()

def display_smart_suggestions(df: pd.DataFrame, categorizer):
    """Display smart pattern suggestions for uncategorized transactions."""
    st.subheader("Smart Pattern Suggestions")

    groups = group_uncategorized(df)
    if not groups:
        st.info("No uncategorized transactions found!")
        return

    for i, group in enumerate(groups):
        with st.expander(f"Group {i+1}: {group['count']} similar transactions (${group['total_amount']:.2f} total)"):
            # Show sample transactions
            st.dataframe(
                pd.DataFrame(group['transactions'])[['description', 'amount']],
                use_container_width=True
            )

            # Show pattern suggestions
            st.write("Suggested Patterns:")
            for suggestion in group['suggestions']:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.code(suggestion['pattern'])
                with col2:
                    st.write(f"Confidence: {suggestion['confidence']:.2f}")
                with col3:
                    if st.button("Use Pattern", key=f"use_pattern_{i}_{suggestion['pattern']}"):
                        # Let user choose category for this pattern
                        category = st.selectbox(
                            "Select category for this pattern:",
                            get_categories(),
                            key=f"category_{i}_{suggestion['pattern']}"
                        )
                        if st.button("Confirm", key=f"confirm_{i}_{suggestion['pattern']}"):
                            categorizer.add_pattern(suggestion['pattern'], category)
                            save_patterns(categorizer)
                            st.success("Pattern added!")
                            st.rerun()

def main():
    """Main pattern management page."""
    st.title("Pattern Management")

    # Load data
    df = load_data()
    if df is None:
        st.error("No transaction data found. Please run process_statements.py first.")
        return

    # Initialize categorizer and categorize transactions
    categorizer = load_categorizer()

    # Store data in session state if not already there
    if st.session_state.data is None:
        df = categorizer.categorize_transactions(df)
        st.session_state.data = df
        # Reset pattern matches cache
        st.session_state.pattern_matches = {}
    else:
        df = st.session_state.data

    # Create tabs for different views
    tab1, tab2 = st.tabs(["Pattern Management", "Smart Suggestions"])

    with tab1:
        manage_patterns(df, categorizer)

    with tab2:
        display_smart_suggestions(df, categorizer)

    # Link to analysis
    st.sidebar.info(
        "Open the Analysis page in a new tab to see the impact of pattern changes:\n\n"
        "Right-click the Analysis page in the sidebar and select 'Open in new tab'"
    )

if __name__ == "__main__":
    main()
