"""
Interactive transaction categorization workflow.
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re
from .rules import RuleBasedCategorizer, CategorizationRule
from .pattern_detector import PatternDetector, RuleSuggestion


@dataclass
class TransactionReview:
    """Data class for transaction review state."""
    transaction: Dict[str, Any]
    suggested_category_id: Optional[int] = None
    matching_rule: Optional[CategorizationRule] = None
    confidence_score: Optional[float] = None


@dataclass
class ReviewSession:
    """Data class for review session state."""
    total_transactions: int
    reviewed_count: int
    remaining_count: int
    current_transaction: Optional[TransactionReview] = None


class InteractiveCategorizer:
    """Handles interactive transaction categorization workflow."""

    def __init__(
        self,
        db_manager,
        rule_categorizer: Optional[RuleBasedCategorizer] = None,
        pattern_detector: Optional[PatternDetector] = None
    ):
        """
        Initialize interactive categorizer.

        Args:
            db_manager: DatabaseManager instance
            rule_categorizer: Optional RuleBasedCategorizer instance
            pattern_detector: Optional PatternDetector instance
        """
        self.db_manager = db_manager
        self.rule_categorizer = rule_categorizer or RuleBasedCategorizer(db_manager)
        self.pattern_detector = pattern_detector or PatternDetector()
        self._reset_session()

    def _reset_session(self) -> None:
        """Reset the review session state."""
        self.session = None
        self.current_suggestions = []

    def start_review_session(self) -> ReviewSession:
        """
        Start a new review session for uncategorized transactions.

        Returns:
            ReviewSession object with initial state
        """
        # Get uncategorized transactions
        transactions = self.db_manager.get_transactions(category_id=None)

        if not transactions:
            return ReviewSession(
                total_transactions=0,
                reviewed_count=0,
                remaining_count=0
            )

        self.session = ReviewSession(
            total_transactions=len(transactions),
            reviewed_count=0,
            remaining_count=len(transactions),
            current_transaction=self._prepare_transaction_review(transactions[0])
        )

        return self.session

    def _prepare_transaction_review(
        self,
        transaction: Dict[str, Any]
    ) -> TransactionReview:
        """Prepare a transaction for review with suggestions."""
        # Try to categorize with existing rules
        category_id = self.rule_categorizer.categorize(
            description=transaction['description'],
            amount=transaction['amount']
        )

        if category_id is not None:
            # Find matching rule for context
            for rule in self.rule_categorizer.rules:
                if rule.category_id == category_id:
                    if rule.is_regex:
                        if re.search(rule.pattern, transaction['description'], re.IGNORECASE):
                            return TransactionReview(
                                transaction=transaction,
                                suggested_category_id=category_id,
                                matching_rule=rule,
                                confidence_score=0.9  # High confidence for existing rules
                            )
                    else:
                        if rule.pattern.upper() in transaction['description'].upper():
                            return TransactionReview(
                                transaction=transaction,
                                suggested_category_id=category_id,
                                matching_rule=rule,
                                confidence_score=0.9
                            )

        return TransactionReview(transaction=transaction)

    def categorize_transaction(
        self,
        transaction_id: int,
        category_id: int
    ) -> Optional[List[RuleSuggestion]]:
        """
        Categorize a transaction and generate rule suggestions.

        Args:
            transaction_id: Transaction ID to categorize
            category_id: Category ID to assign

        Returns:
            List of rule suggestions if any are generated
        """
        if not self.session or not self.session.current_transaction:
            raise ValueError("No active review session")

        # Update transaction category
        self.db_manager.update_transaction_category(transaction_id, category_id)

        # Get similar transactions for pattern analysis
        similar_transactions = self._find_similar_transactions(
            self.session.current_transaction.transaction
        )

        # Generate rule suggestions
        suggestions = self.pattern_detector.analyze_transactions(
            transactions=similar_transactions,
            category_id=category_id
        )
        self.current_suggestions = suggestions

        # Update session state
        self.session.reviewed_count += 1
        self.session.remaining_count -= 1

        # Get next transaction if any remain
        if self.session.remaining_count > 0:
            next_transactions = self.db_manager.get_transactions(category_id=None)
            if next_transactions:
                self.session.current_transaction = self._prepare_transaction_review(
                    next_transactions[0]
                )
            else:
                self.session.current_transaction = None
        else:
            self.session.current_transaction = None

        return suggestions if suggestions else None

    def _find_similar_transactions(
        self,
        transaction: Dict[str, Any],
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Find transactions with similar descriptions."""
        # Get keywords from the transaction description
        keywords = self.pattern_detector.text_analyzer.extract_keywords(
            transaction['description']
        )

        similar_transactions = []
        seen_ids = set()

        # Search for transactions with similar keywords
        for keyword in keywords:
            if len(keyword) < 3:
                continue

            # Use SQL LIKE for basic pattern matching
            matches = self.db_manager.get_transactions_by_pattern(
                f"%{keyword}%",
                exclude_ids=list(seen_ids),
                limit=limit
            )

            for tx in matches:
                if tx['id'] not in seen_ids:
                    similar_transactions.append(tx)
                    seen_ids.add(tx['id'])

                if len(similar_transactions) >= limit:
                    break

            if len(similar_transactions) >= limit:
                break

        return similar_transactions

    def add_rule(self, suggestion: RuleSuggestion) -> None:
        """
        Add a rule from a suggestion.

        Args:
            suggestion: RuleSuggestion to convert to a rule
        """
        self.db_manager.add_rule(
            pattern=suggestion.pattern,
            category_id=suggestion.category_id,
            is_regex=suggestion.is_regex
        )
        self.rule_categorizer._refresh_rules()

    def skip_transaction(self) -> None:
        """Skip the current transaction and move to the next one."""
        if not self.session or not self.session.current_transaction:
            raise ValueError("No active review session")

        # Get next transaction
        next_transactions = self.db_manager.get_transactions(category_id=None)
        if next_transactions:
            self.session.current_transaction = self._prepare_transaction_review(
                next_transactions[0]
            )
        else:
            self.session.current_transaction = None

    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        if not self.session:
            return {
                "total": 0,
                "reviewed": 0,
                "remaining": 0,
                "progress": 0.0
            }

        return {
            "total": self.session.total_transactions,
            "reviewed": self.session.reviewed_count,
            "remaining": self.session.remaining_count,
            "progress": (
                self.session.reviewed_count / self.session.total_transactions
                if self.session.total_transactions > 0
                else 0.0
            )
        }
