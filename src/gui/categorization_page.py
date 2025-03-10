"""
Streamlit page for interactive transaction categorization.
"""
import streamlit as st
from typing import Dict, Any
from src.categorization.interactive import InteractiveCategorizer, RuleSuggestion
from src.categorization.rules import RuleBasedCategorizer
from src.database.categories import CategoryManager
from src.database.rules import RuleManager
from src.database.transactions import TransactionManager


def format_transaction(transaction: Dict[str, Any]) -> str:
    """Format transaction details for display."""
    # Format amount with color based on type
    amount = transaction['amount']
    amount_color = "red" if amount > 0 else "green"
    amount_str = f":{amount_color}[${abs(amount):,.2f}]"

    return (
        f"**Date:** {transaction['date']}\n\n"
        f"**Description:** {transaction['description']}\n\n"
        f"**Amount:** {amount_str}\n\n"
        f"**Reference:** {transaction.get('reference_number', 'N/A')}"
    )


def format_rule_suggestion(suggestion: RuleSuggestion) -> str:
    """Format rule suggestion for display."""
    # Color code confidence score
    confidence = suggestion.confidence_score
    if confidence >= 0.9:
        confidence_color = "green"
    elif confidence >= 0.7:
        confidence_color = "orange"
    else:
        confidence_color = "red"

    matches = "\n".join(
        f"- {match} "
        f"(:blue[${tx['amount']:,.2f}])"
        for match, tx in zip(
            suggestion.sample_matches[:3],
            suggestion.matching_transactions[:3]
        )
    )

    return (
        f"**Pattern:** `{suggestion.pattern}`\n\n"
        f"**Type:** {'Regex' if suggestion.is_regex else 'Simple'}\n\n"
        f"**Confidence:** :{confidence_color}[{confidence:.0%}]\n\n"
        f"**Sample Matches:**\n{matches}\n\n"
        f"**Total Matches:** {len(suggestion.matching_transactions)} transaction(s)"
    )


def render_categorization_page(
    transaction_manager: TransactionManager,
    category_manager: CategoryManager,
    rule_manager: RuleManager
) -> None:
    """Render the interactive categorization page."""
    st.title("Transaction Categorization")

    # Initialize session state
    if "categorizer" not in st.session_state:
        st.session_state.categorizer = InteractiveCategorizer(
            transaction_manager,
            rule_categorizer=RuleBasedCategorizer(rule_manager)
        )
        st.session_state.review_session = None
        st.session_state.current_suggestions = []

    # Start/Reset button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Start/Reset Session"):
            st.session_state.review_session = st.session_state.categorizer.start_review_session()
            st.session_state.current_suggestions = []
            st.rerun()

    # Show session stats if active
    if st.session_state.review_session:
        stats = st.session_state.categorizer.get_session_stats()
        with col2:
            st.progress(stats["progress"], f"Progress: {stats['reviewed']}/{stats['total']}")

    # Main categorization interface
    if (st.session_state.review_session and
        st.session_state.review_session.current_transaction):

        # Transaction details
        st.header("Current Transaction")
        transaction = st.session_state.review_session.current_transaction.transaction
        st.markdown(format_transaction(transaction))

        # Category selection with search
        categories = category_manager.get_category_hierarchy()

        # Group categories by top level
        category_groups = {}
        for cat in categories:
            top_level = cat["path"].split(" > ")[0]
            if top_level not in category_groups:
                category_groups[top_level] = []
            category_groups[top_level].append(cat)

        # Two-step selection
        col1, col2 = st.columns(2)
        with col1:
            top_level = st.selectbox(
                "Category Group",
                options=sorted(category_groups.keys()),
                index=None,
                placeholder="Select group..."
            )

        with col2:
            if top_level:
                sub_categories = {
                    cat["path"]: cat["id"]
                    for cat in category_groups[top_level]
                }
                selected_category = st.selectbox(
                    "Specific Category",
                    options=list(sub_categories.keys()),
                    index=None,
                    placeholder="Choose category..."
                )
            else:
                selected_category = None

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("Skip", use_container_width=True):
                st.session_state.categorizer.skip_transaction()
                st.session_state.current_suggestions = []
                st.rerun()

        with col2:
            if selected_category and st.button(
                "Confirm Category",
                type="primary",
                use_container_width=True
            ):
                category_id = sub_categories[selected_category]
                suggestions = st.session_state.categorizer.categorize_transaction(
                    transaction["id"],
                    category_id
                )
                if suggestions:
                    st.session_state.current_suggestions = suggestions
                st.rerun()

        # Show keyboard shortcuts help
        with st.expander("⌨️ Keyboard Shortcuts"):
            st.markdown("""
            - **Enter** - Confirm category
            - **Space** - Skip transaction
            - **↑/↓** - Navigate categories
            """)

        # Show rule suggestions with better organization
        if st.session_state.current_suggestions:
            st.header("📋 Suggested Rules")

            # Group suggestions by confidence
            high_confidence = []
            medium_confidence = []
            low_confidence = []

            for suggestion in st.session_state.current_suggestions:
                if suggestion.confidence_score >= 0.9:
                    high_confidence.append(suggestion)
                elif suggestion.confidence_score >= 0.7:
                    medium_confidence.append(suggestion)
                else:
                    low_confidence.append(suggestion)

            # Display suggestions by confidence group
            if high_confidence:
                st.subheader("✅ :green[High Confidence Rules]")
                for i, suggestion in enumerate(high_confidence):
                    with st.expander(
                        f"Rule {i + 1}: {suggestion.pattern} "
                        f"(:green[{suggestion.confidence_score:.0%}] confidence)"
                    ):
                        st.markdown(format_rule_suggestion(suggestion))
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if st.button("Add Rule", key=f"add_rule_high_{i}"):
                                st.session_state.categorizer.add_rule(suggestion)
                                st.success("Rule added successfully!")

            if medium_confidence:
                st.subheader("⚠️ :orange[Medium Confidence Rules]")
                for i, suggestion in enumerate(medium_confidence):
                    with st.expander(
                        f"Rule {i + 1}: {suggestion.pattern} "
                        f"(:orange[{suggestion.confidence_score:.0%}] confidence)"
                    ):
                        st.markdown(format_rule_suggestion(suggestion))
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if st.button("Add Rule", key=f"add_rule_med_{i}"):
                                st.session_state.categorizer.add_rule(suggestion)
                                st.success("Rule added successfully!")

            if low_confidence:
                st.subheader("❗ :red[Low Confidence Rules]")
                for i, suggestion in enumerate(low_confidence):
                    with st.expander(
                        f"Rule {i + 1}: {suggestion.pattern} "
                        f"(:red[{suggestion.confidence_score:.0%}] confidence)"
                    ):
                        st.markdown(format_rule_suggestion(suggestion))
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if st.button("Add Rule", key=f"add_rule_low_{i}"):
                                st.session_state.categorizer.add_rule(suggestion)
                                st.success("Rule added successfully!")

    elif st.session_state.review_session:
        st.success("🎉 All transactions have been reviewed!")
        if st.button("Start New Session"):
            st.session_state.review_session = st.session_state.categorizer.start_review_session()
            st.session_state.current_suggestions = []
            st.rerun()
    else:
        st.info("👋 Click 'Start/Reset Session' to begin reviewing transactions.")

        # Show sample transaction format
        with st.expander("ℹ️ About Transaction Categorization"):
            st.markdown("""
            This tool helps you:
            1. Review uncategorized transactions one by one
            2. Assign categories quickly and efficiently
            3. Get smart rule suggestions based on your choices
            4. Build a consistent categorization system

            Rules are automatically suggested based on patterns in your categorization choices.
            High confidence rules can be applied automatically to future transactions.
            """)
