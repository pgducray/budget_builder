"""
Text analysis functionality for transaction categorization.
"""
from typing import List
import re


class TextAnalyzer:
    """Handles text analysis for improved categorization."""

    def __init__(self):
        """Initialize text analyzer with common words and patterns."""
        self.common_transaction_words = {
            'PAYMENT', 'PURCHASE', 'POS', 'DEBIT', 'CREDIT', 'TRANSACTION',
            'WITHDRAWAL', 'DEPOSIT', 'FEE', 'CHARGE', 'ACH', 'TRANSFER'
        }

        self.business_suffixes = [
            'INC', 'LLC', 'LTD', 'CORP', 'CORPORATION', 'CO',
            'INCORPORATED', 'LIMITED', 'COMPANY'
        ]

    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract relevant keywords from transaction description.

        Args:
            text: Transaction description

        Returns:
            List of extracted keywords
        """
        # Convert to uppercase for consistency
        text = text.upper()

        # Remove special characters and split
        words = re.sub(r'[^\w\s]', ' ', text).split()

        # Filter out common words and short strings
        keywords = [
            word for word in words
            if word not in self.common_transaction_words and len(word) > 2
        ]

        return keywords

    def normalize_vendor_name(self, vendor: str) -> str:
        """
        Normalize vendor name for consistent matching.

        Args:
            vendor: Raw vendor name

        Returns:
            Normalized vendor name
        """
        # Convert to uppercase
        normalized = vendor.upper()

        # Remove business suffixes
        for suffix in self.business_suffixes:
            normalized = re.sub(rf'\b{suffix}\b\.?', '', normalized)

        # Replace special characters with spaces, but keep * for compound patterns
        normalized = re.sub(r'[^\w\s\*]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)

        # Special handling for compound patterns (e.g., UBER*EATS)
        if '*' in normalized:
            parts = normalized.split('*')
            normalized = ' '.join(parts)

        return normalized.strip()

    def find_common_patterns(self, descriptions: List[str]) -> List[str]:
        """
        Find common patterns in transaction descriptions.

        Args:
            descriptions: List of transaction descriptions

        Returns:
            List of common patterns found
        """
        # Convert all descriptions to uppercase and normalize
        normalized_descriptions = [
            self.normalize_vendor_name(desc)
            for desc in descriptions
        ]

        # Extract keywords from each description
        all_keywords = [
            self.extract_keywords(desc)
            for desc in normalized_descriptions
        ]

        # Find keywords that appear frequently
        keyword_counts = {}
        for keywords in all_keywords:
            for keyword in keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        # Return patterns that appear in at least 20% of transactions
        min_occurrences = max(2, len(descriptions) // 5)
        common_patterns = [
            keyword
            for keyword, count in keyword_counts.items()
            if count >= min_occurrences
        ]

        return sorted(common_patterns, key=lambda x: keyword_counts[x], reverse=True)

    def suggest_regex_patterns(self, descriptions: List[str]) -> List[str]:
        """
        Suggest regex patterns based on transaction descriptions.

        Args:
            descriptions: List of transaction descriptions

        Returns:
            List of suggested regex patterns
        """
        patterns = []

        # Find common prefixes
        normalized_descriptions = [
            self.normalize_vendor_name(desc)
            for desc in descriptions
        ]

        # Group by first word
        prefixes = {}
        for desc in normalized_descriptions:
            words = desc.split()
            if words:
                prefix = words[0]
                if len(prefix) > 2:  # Ignore short prefixes
                    prefixes[prefix] = prefixes.get(prefix, 0) + 1

        # Add common prefixes as patterns
        min_occurrences = max(2, len(descriptions) // 5)
        for prefix, count in prefixes.items():
            if count >= min_occurrences:
                patterns.append(f"^{prefix}")

        # Find common number patterns
        number_patterns = {
            r'\d{4}': 'four digits',
            r'\d{6}': 'six digits',
            r'\d{2}/\d{2}': 'date (MM/DD)',
            r'\#\d+': 'number with hash'
        }

        for desc in normalized_descriptions:
            for pattern in number_patterns:
                if re.search(pattern, desc):
                    patterns.append(pattern)

        return list(set(patterns))  # Remove duplicates
