"""
Shared components and utilities for Streamlit pages.
"""
import streamlit as st
import pandas as pd
from typing import Tuple, Optional, Dict
from src.utils import (
    load_data, load_categorizer, save_patterns,
    check_pattern_updates
)

def create_page_config(title: str):
    """Create consistent page config across pages."""
    return st.set_page_config(
        page_title=title,
        layout="wide",
        initial_sidebar_state="expanded"
    )

def display_data_error():
    """Consistent error message for missing data."""
    return st.error("No transaction data found. Please run process_statements.py first.")

def load_app_data() -> Tuple[Optional[pd.DataFrame], Optional[object]]:
    """Centralized data loading with caching."""
    if check_pattern_updates() or st.session_state.data is None:
        df = load_data()
        if df is None:
            return None, None

        categorizer = load_categorizer()
        df = categorizer.categorize_transactions(df)
        st.session_state.data = df
        st.session_state.categorizer = categorizer
        st.session_state.pattern_matches = {}

    return st.session_state.data, st.session_state.categorizer

class PatternManager:
    """Encapsulate pattern management logic."""
    def __init__(self, df: pd.DataFrame, categorizer):
        self.df = df
        self.categorizer = categorizer

    def preview_pattern(self, pattern: str, category: str) -> pd.DataFrame:
        """Preview pattern matches."""
        matches = self.df[self.df['description'].str.contains(pattern, case=False, regex=True)]
        return matches[['description', 'amount', 'Category']].head()

    def save_pattern(self, old_pattern: str, new_pattern: str, category: str):
        """Save pattern changes."""
        if old_pattern:
            self.categorizer.remove_pattern(old_pattern)
        self.categorizer.add_pattern(new_pattern, category)
        save_patterns(self.categorizer)

    def get_pattern_matches(self, pattern: str) -> int:
        """Get number of matches for a pattern."""
        if pattern not in st.session_state.pattern_matches:
            match_count = len(self.df[self.df['description'].str.contains(pattern, case=False, regex=True)])
            st.session_state.pattern_matches[pattern] = match_count
        return st.session_state.pattern_matches[pattern]

class TransactionAnalyzer:
    """Encapsulate analysis logic."""
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def get_filtered_data(self, category: str = 'All', search: str = '') -> pd.DataFrame:
        """Apply filters to data."""
        filtered = self.df.copy()
        if category != 'All':
            filtered = filtered[filtered['Category'] == category]
        if search:
            filtered = filtered[filtered['description'].str.contains(search, case=False)]
        return filtered

    def get_category_stats(self) -> Dict:
        """Calculate category statistics."""
        total = len(self.df)
        uncategorized = len(self.df[self.df['Category'] == 'Uncategorized'])
        return {
            'total': total,
            'categorized_pct': ((total - uncategorized)/total)*100,
            'uncategorized': uncategorized
        }

    def get_category_distribution(self) -> pd.Series:
        """Get category distribution for charts."""
        return self.df['Category'].value_counts()
