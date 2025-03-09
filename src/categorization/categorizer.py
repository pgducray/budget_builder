"""
Main transaction categorization functionality.
"""
from typing import List, Dict, Any, Optional
from .rules import RuleBasedCategorizer
from .ml import MLCategorizer


class TransactionCategorizer:
    """
    Main categorizer that combines rule-based and ML approaches.

    The categorizer first attempts to match transactions using rules.
    If no rule matches and ML categorization is enabled, it falls back
    to ML-based prediction.
    """

    def __init__(
        self,
        db_manager,
        enable_ml: bool = False,
        model_path: Optional[str] = None
    ):
        """
        Initialize categorizer.

        Args:
            db_manager: DatabaseManager instance
            enable_ml: Whether to enable ML-based categorization
            model_path: Optional path to ML model
        """
        self.rule_categorizer = RuleBasedCategorizer(db_manager)
        self.ml_categorizer = MLCategorizer(model_path) if enable_ml else None

    def categorize_transaction(
        self,
        description: str,
        amount: float,
        vendor: Optional[str] = None
    ) -> Optional[int]:
        """
        Categorize a single transaction.

        Args:
            description: Transaction description
            amount: Transaction amount
            vendor: Optional vendor name

        Returns:
            Category ID if match found, None otherwise
        """
        # Try rule-based categorization first
        category_id = self.rule_categorizer.categorize(
            description=description,
            amount=amount,
            vendor=vendor
        )

        # If no rule matches and ML is enabled, try ML prediction
        if category_id is None and self.ml_categorizer:
            predictions = self.ml_categorizer.predict_category(
                description=description,
                amount=amount,
                vendor=vendor
            )
            if predictions:
                # Use the category with highest confidence
                category_id = max(predictions.items(), key=lambda x: x[1])[0]

        return category_id

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
        categorized = []

        for transaction in transactions:
            tx = transaction.copy()
            category_id = self.categorize_transaction(
                description=tx.get('description', ''),
                amount=tx.get('amount', 0.0),
                vendor=tx.get('vendor')
            )
            tx['category_id'] = category_id
            categorized.append(tx)

        return categorized

    @classmethod
    def migrate_from_json(
        cls,
        db_manager,
        json_path: str,
        clear_existing: bool = False,
        enable_ml: bool = False,
        model_path: Optional[str] = None
    ) -> "TransactionCategorizer":
        """
        Create a categorizer and migrate rules from JSON.

        Args:
            db_manager: DatabaseManager instance
            json_path: Path to JSON file containing rules
            clear_existing: Whether to clear existing rules
            enable_ml: Whether to enable ML-based categorization
            model_path: Optional path to ML model

        Returns:
            New TransactionCategorizer instance
        """
        # Create categorizer
        categorizer = cls(
            db_manager=db_manager,
            enable_ml=enable_ml,
            model_path=model_path
        )

        # Migrate rules
        RuleBasedCategorizer.migrate_from_json(
            db_manager=db_manager,
            json_path=json_path,
            clear_existing=clear_existing
        )

        return categorizer
