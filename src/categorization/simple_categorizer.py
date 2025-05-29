"""
Simple rule-based transaction categorizer.
"""
from typing import Dict, List, Optional
import pandas as pd
import re

class SimpleTransactionCategorizer:
    """Categorizes transactions based on simple pattern matching rules."""

    # Default category mappings
    MERCHANT_PATTERNS = {
        r'(?i)(COFFEE|CAFE|ARTISAN COFFEE|GONG CHA)': 'Coffee Shops',
        r'(?i)(RESTAURANT|FUSION CUIS|FOOD|SENSEI|SUSHI|PIZZA)': 'Restaurants',
        r'(?i)(INTERMART|SUPERMARKET|MARKET|WINNER\'S)': 'Groceries',
        r'(?i)(SALE SUCRE|DELIGHTIO)': 'Shopping',
        r'(?i)(SHELL|ENGEN|FILLING STATIO)': 'Fuel',
        r'(?i)Service Fee': 'Bank Charges',
        r'(?i)Tax Amount': 'Taxes',
    }

    TRANSACTION_TYPE_PATTERNS = {
        r'(?i)salary': 'Income',
        r'(?i)ATM Cash Withdrawal': 'Cash Withdrawal',
        r'(?i)Debit Card Purchase': 'Card Payment',
        r'(?i)(Transfer|Payment|Account Transfer)': 'Transfer',
        r'(?i)Interbank Transfer': 'Bank Transfer',
    }

    def __init__(
        self,
        merchant_patterns: Optional[Dict[str, str]] = None,
        transaction_type_patterns: Optional[Dict[str, str]] = None
    ):
        """
        Initialize with optional custom pattern mappings.

        Args:
            merchant_patterns: Custom merchant name regex patterns to categories
            transaction_type_patterns: Custom transaction type regex patterns to categories
        """
        self.merchant_patterns = merchant_patterns or self.MERCHANT_PATTERNS
        self.transaction_type_patterns = transaction_type_patterns or self.TRANSACTION_TYPE_PATTERNS

    def categorize_transaction(self, description: str) -> str:
        """
        Categorize a single transaction based on its description.

        Args:
            description: Transaction description text

        Returns:
            Category name as string
        """
        # First try to match transaction type patterns
        for pattern, category in self.transaction_type_patterns.items():
            if re.search(pattern, description):
                # For general transaction types, also check for merchant patterns
                if category in ['Card Payment', 'Transfer']:
                    for m_pattern, m_category in self.merchant_patterns.items():
                        if re.search(m_pattern, description):
                            return m_category
                return category

        # Then try merchant patterns
        for pattern, category in self.merchant_patterns.items():
            if re.search(pattern, description):
                return category

        return 'Uncategorized'

    def categorize_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Categorize all transactions in a DataFrame.

        Args:
            df: DataFrame with 'description' column

        Returns:
            DataFrame with added 'Category' column
        """
        df = df.copy()
        df['Category'] = df['description'].apply(self.categorize_transaction)
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
