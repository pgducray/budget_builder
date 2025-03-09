"""
Rule-based categorization functionality.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
from .text import TextAnalyzer


@dataclass
class CategorizationRule:
    """Data class for categorization rules."""
    pattern: str
    category_id: int
    priority: int = 0
    is_regex: bool = False


class RuleBasedCategorizer:
    """Handles rule-based transaction categorization."""

    def __init__(self, db_manager):
        """
        Initialize categorizer with database manager.

        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
        self.text_analyzer = TextAnalyzer()
        self._refresh_rules()

    def _refresh_rules(self) -> None:
        """Refresh rules from database."""
        db_rules = self.db_manager.get_rules()
        self.rules = [
            CategorizationRule(
                pattern=rule["pattern"],
                category_id=rule["category_id"],
                priority=rule["priority"],
                is_regex=rule["is_regex"]
            )
            for rule in db_rules
        ]

    def categorize(
        self,
        description: str,
        amount: float,
        vendor: Optional[str] = None
    ) -> Optional[int]:
        """
        Categorize a transaction using rules.

        Args:
            description: Transaction description
            amount: Transaction amount
            vendor: Optional vendor name

        Returns:
            Category ID if match found, None otherwise
        """
        # Normalize text for better matching
        normalized_desc = self.text_analyzer.normalize_vendor_name(description.upper())

        if vendor:
            normalized_vendor = self.text_analyzer.normalize_vendor_name(vendor.upper())
            # Combine description and vendor for matching
            text_to_match = f"{normalized_desc} {normalized_vendor}"
        else:
            text_to_match = normalized_desc

        # Check each rule in priority order
        for rule in self.rules:
            if rule.is_regex:
                if re.search(rule.pattern, text_to_match, re.IGNORECASE):
                    return rule.category_id
            else:
                if rule.pattern.upper() in text_to_match:
                    return rule.category_id

        return None

    def categorize_batch(
        self,
        transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Categorize multiple transactions.

        Args:
            transactions: List of transaction dictionaries

        Returns:
            Transactions with added category IDs
        """
        categorized_transactions = []

        for transaction in transactions:
            # Create a copy to avoid modifying original
            tx = transaction.copy()

            category_id = self.categorize(
                description=tx.get('description', ''),
                amount=tx.get('amount', 0.0),
                vendor=tx.get('vendor')
            )

            tx['category_id'] = category_id
            categorized_transactions.append(tx)

        return categorized_transactions

    @classmethod
    def migrate_from_json(
        cls,
        db_manager,
        json_path: str,
        clear_existing: bool = False
    ) -> "RuleBasedCategorizer":
        """
        Migrate rules from JSON file to database.

        Args:
            db_manager: DatabaseManager instance
            json_path: Path to JSON file containing rules
            clear_existing: Whether to clear existing rules

        Returns:
            New RuleBasedCategorizer instance
        """
        import json

        with open(json_path, "r") as f:
            config = json.load(f)

        db_manager.import_rules(
            rules=config.get("rules", []),
            clear_existing=clear_existing
        )

        return cls(db_manager)
