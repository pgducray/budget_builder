"""
Home page for the Transaction Categorizer application.
"""
import streamlit as st

st.set_page_config(
    page_title="Transaction Categorizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main home page."""
    st.title("Transaction Categorizer")

    st.write("""
    Welcome to the Transaction Categorizer! This tool helps you analyze and categorize your financial transactions.

    ## Features

    ### 📊 Analysis
    - View and filter transactions
    - See category statistics
    - Analyze transaction frequency
    - Export categorized data

    ### ⚙️ Pattern Management
    - View current categorization patterns
    - Add new patterns with live preview
    - Remove patterns and see impact
    - Auto-save and instant categorization

    ## Getting Started

    1. First, ensure you have run `process_statements.py` to create your transaction database
    2. Open both the Analysis and Pattern Management pages in separate tabs
    3. Use Pattern Management to define and refine your categorization patterns
    4. Watch the results update in real-time in the Analysis page

    ## Tips

    - Keep both pages open in separate tabs for the best workflow
    - Use the pattern preview feature to test new patterns before adding them
    - Check the frequency analysis to identify common transactions that need patterns
    """)

    # Quick links
    st.sidebar.title("Quick Links")
    st.sidebar.info(
        "Open pages in new tabs for better workflow:\n\n"
        "1. Right-click Analysis in the sidebar and select 'Open in new tab'\n"
        "2. Right-click Pattern Management in the sidebar and select 'Open in new tab'"
    )

if __name__ == "__main__":
    main()
