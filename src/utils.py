"""
Shared utilities for Streamlit pages.
"""
import time
import pandas as pd
import streamlit as st
from pathlib import Path
from src.categorization.simple_categorizer import SimpleTransactionCategorizer
from src.config import CATEGORIES

def init_session_state():
    """Initialize session state variables."""
    if 'data' not in st.session_state:
        st.session_state.data = None
        st.session_state.categorizer = None
    if 'last_pattern_update' not in st.session_state:
        st.session_state.last_pattern_update = time.time()
    if 'editing_pattern' not in st.session_state:
        st.session_state.editing_pattern = None
        st.session_state.editing_category = None
    if 'preview_pattern' not in st.session_state:
        st.session_state.preview_pattern = None
        st.session_state.preview_category = None
    if 'pattern_matches' not in st.session_state:
        st.session_state.pattern_matches = {}

def update_pattern_matches(df: pd.DataFrame, old_pattern: str, new_pattern: str, category: str) -> pd.DataFrame:
    """Update pattern matches efficiently."""
    # Initialize Matching Pattern column if it doesn't exist
    if 'Matching Pattern' not in df.columns:
        df['Matching Pattern'] = None
        df['Category'] = 'Uncategorized'

    # Reset old pattern matches
    if old_pattern:
        affected_rows = df['Matching Pattern'] == old_pattern
        df.loc[affected_rows, 'Category'] = 'Uncategorized'
        df.loc[affected_rows, 'Matching Pattern'] = None

    # Apply new pattern
    new_matches = df['description'].str.contains(new_pattern, case=False, regex=True)
    df.loc[new_matches, 'Category'] = category
    df.loc[new_matches, 'Matching Pattern'] = new_pattern

    return df

def get_categories() -> list:
    """Get list of available categories."""
    return CATEGORIES

def check_pattern_updates() -> bool:
    """Check if patterns have been updated recently."""
    patterns_path = Path("data/patterns.json")
    if not patterns_path.exists():
        return False

    # Get file modification time
    mtime = patterns_path.stat().st_mtime
    return mtime > st.session_state.last_pattern_update

def update_pattern_timestamp():
    """Update the last pattern change timestamp."""
    st.session_state.last_pattern_update = time.time()

def load_data() -> pd.DataFrame:
    """Load transaction data if available."""
    transactions_path = Path("data/transactions.csv")
    if transactions_path.exists():
        df = pd.read_csv(transactions_path)
        if 'Matching Pattern' not in df.columns:
            df['Matching Pattern'] = None
            df['Category'] = 'Uncategorized'
        return df
    return None

def load_categorizer() -> SimpleTransactionCategorizer:
    """Initialize categorizer with patterns."""
    patterns_path = Path("data/patterns.json")
    return SimpleTransactionCategorizer(
        SimpleTransactionCategorizer.load_patterns(patterns_path)
    )

def save_patterns(categorizer: SimpleTransactionCategorizer) -> None:
    """Save patterns and trigger re-categorization."""
    patterns_path = Path("data/patterns.json")
    categorizer.save_patterns(patterns_path)
    update_pattern_timestamp()

def get_frequent_transactions(df: pd.DataFrame, category: str, limit: int = 10) -> pd.DataFrame:
    """Get most frequent transactions for a category."""
    if category == 'All':
        transactions = df
    else:
        transactions = df[df['Category'] == category]

    # Group by description and calculate frequency and total amount
    frequent = (
        transactions.groupby('description')
        .agg({
            'amount': ['count', 'sum']
        })
        .round(2)
    )
    frequent.columns = ['Count', 'Total Amount']
    return frequent.nlargest(limit, 'Count')
