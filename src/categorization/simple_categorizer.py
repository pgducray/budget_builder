"""
Simple rule-based transaction categorizer.
"""
from typing import Dict, Optional, Tuple
import json
from pathlib import Path
import pandas as pd
import re

class SimpleTransactionCategorizer:
    """Categorizes transactions based on simple pattern matching rules."""

    # Default category mappings ordered from most specific to most general
    PATTERNS = {
        # Specific transaction types
        r'(?i)salary': 'Income',
        r'(?i)ATM Cash Withdrawal': 'Cash Withdrawal',
        r'(?i)Interbank Transfer': 'Bank Transfer',
        r'(?i)Service Fee': 'Bank Charges',
        r'(?i)Tax Amount': 'Taxes',

        # Merchant patterns
        r'(?i)(COFFEE|CAFE|ARTISAN COFFEE|GONG CHA)': 'Coffee Shops',
        r'(?i)(RESTAURANT|FUSION CUIS|FOOD|SENSEI|SUSHI|PIZZA)': 'Restaurants',
        r'(?i)(INTERMART|SUPERMARKET|MARKET|WINNER\'S)': 'Groceries',
        r'(?i)(SALE SUCRE|DELIGHTIO)': 'Shopping',
        r'(?i)(SHELL|ENGEN|FILLING STATIO)': 'Fuel',

        # Most general patterns
        r'(?i)(Transfer|Payment|Account Transfer)': 'Transfer',
        r'(?i)Debit Card Purchase': 'Card Payment',
    }

    def __init__(self, patterns: Optional[Dict[str, str]] = None):
        """
        Initialize with optional custom pattern mappings.

        Args:
            patterns: Custom regex patterns to categories mapping, ordered from most specific to most general
        """
        self.patterns = patterns or self.PATTERNS

    @classmethod
    def load_patterns(cls, path: str) -> Dict[str, str]:
        """Load patterns from a JSON file."""
        path = Path(path)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return cls.PATTERNS

    def save_patterns(self, path: str) -> None:
        """Save current patterns to a JSON file."""
        with open(path, 'w') as f:
            json.dump(self.patterns, f, indent=4)

    def add_pattern(self, pattern: str, category: str) -> None:
        """Add a new pattern-category mapping."""
        self.patterns[pattern] = category

    def remove_pattern(self, pattern: str) -> None:
        """Remove a pattern from the mappings."""
        if pattern in self.patterns:
            del self.patterns[pattern]

    def categorize_transaction(self, description: str) -> Tuple[str, Optional[str]]:
        """
        Categorize a single transaction based on its description.

        Args:
            description: Transaction description text

        Returns:
            Tuple of (category name, matching pattern or None if uncategorized)
        """
        for pattern, category in self.patterns.items():
            if re.search(pattern, description):
                return category, pattern

        return 'Uncategorized', None

    def categorize_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Categorize all transactions in a DataFrame.

        Args:
            df: DataFrame with 'description' column

        Returns:
            DataFrame with added 'Category' and 'Matching Pattern' columns
        """
        df = df.copy()
        results = df['description'].apply(self.categorize_transaction)
        df['Category'] = results.apply(lambda x: x[0])
        df['Matching Pattern'] = results.apply(lambda x: x[1])
        return df

    def get_category_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate summary of spending by category.

        Args:
            df: DataFrame with 'Category' and 'amount' columns

        Returns:
            DataFrame with category summaries
        """
        # Group by category
        summary = df.groupby('Category').agg({
            'amount': ['sum', 'count']
        }).round(2)

        # Flatten column names
        summary.columns = ['Total Amount', 'Transaction Count']

        return summary.sort_values('Total Amount', ascending=False)
