"""
Pattern management page.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from src.utils import (
    get_categories, init_session_state
)
from src.analysis import (
    group_uncategorized, suggest_pattern,
    analyze_pattern_effectiveness
)
from src.config import DISPLAY_CONFIG
from src.shared.components import (
    create_page_config, display_data_error,
    load_app_data, PatternManager
)

# Initialize session state
init_session_state()

# Set up page
create_page_config("Pattern Management")

def display_pattern_preview(pattern_manager: PatternManager, pattern: str, category: str):
    """Display preview of transactions that would match a new pattern."""
    matches = pattern_manager.preview_pattern(pattern, category)
    if not matches.empty:
        st.write(f"Preview: {len(matches)} matching transactions found")
        st.dataframe(
            matches[DISPLAY_CONFIG['preview_columns']],
            use_container_width=True
        )
    else:
        st.warning("No matching transactions found")

def edit_pattern(pattern_manager: PatternManager, pattern: str, category: str):
    """Edit an existing pattern."""
    st.session_state.editing_pattern = pattern
    st.session_state.editing_category = category

    # Pattern input
    col1, col2, col3 = st.columns(DISPLAY_CONFIG['pattern_list_widths'][:3])
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
            display_pattern_preview(pattern_manager, new_pattern, new_category)

    # Save/Cancel buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Changes"):
            if pattern != new_pattern or category != new_category:
                pattern_manager.save_pattern(pattern, new_pattern, new_category)
                st.success("Pattern saved! Refresh Analysis page to see changes.")
                st.session_state.editing_pattern = None
                st.session_state.preview_pattern = None
                st.rerun()
    with col2:
        if st.button("Cancel"):
            st.session_state.editing_pattern = None
            st.session_state.preview_pattern = None
            st.rerun()

def manage_patterns(pattern_manager: PatternManager):
    """Pattern management interface with live preview."""
    st.subheader("Current Patterns")

    # Display patterns using cached counts
    patterns_data = [
        {
            'Pattern': pattern,
            'Category': category,
            'Matching Transactions': pattern_manager.get_pattern_matches(pattern)
        }
        for pattern, category in pattern_manager.categorizer.patterns.items()
    ]

    patterns_df = pd.DataFrame(patterns_data)

    # Display patterns with edit buttons
    for idx, row in patterns_df.iterrows():
        col1, col2, col3, col4 = st.columns(DISPLAY_CONFIG['pattern_list_widths'])
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
            pattern_manager,
            st.session_state.editing_pattern,
            st.session_state.editing_category
        )

    # Add new pattern
    st.markdown("---")
    st.subheader("Add New Pattern")

    col1, col2, col3 = st.columns(DISPLAY_CONFIG['pattern_list_widths'][:3])
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
            display_pattern_preview(pattern_manager, new_pattern, new_category)

    if st.button("Add Pattern") and new_pattern:
        pattern_manager.save_pattern(None, new_pattern, new_category)
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
    df, categorizer = load_app_data()
    if df is None:
        display_data_error()
        return

    # Create pattern manager
    pattern_manager = PatternManager(df, categorizer)

    # Create tabs for different views
    tab1, tab2 = st.tabs(["Pattern Management", "Smart Suggestions"])

    with tab1:
        manage_patterns(pattern_manager)

    with tab2:
        display_smart_suggestions(df, categorizer)

    # Link to analysis
    st.sidebar.info(
        "Open the Analysis page in a new tab to see the impact of pattern changes:\n\n"
        "Right-click the Analysis page in the sidebar and select 'Open in new tab'"
    )

if __name__ == "__main__":
    main()
