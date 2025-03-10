"""
Pattern detection and rule suggestion functionality.
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import re
from .text import TextAnalyzer


@dataclass
class RuleSuggestion:
    """Data class for rule suggestions."""
    pattern: str
    category_id: int
    is_regex: bool
    confidence_score: float
    matching_transactions: List[Dict[str, Any]]
    sample_matches: List[str]


class PatternDetector:
    """Detects patterns in transaction descriptions and suggests rules."""

    def __init__(self, text_analyzer: Optional[TextAnalyzer] = None):
        """
        Initialize pattern detector.

        Args:
            text_analyzer: Optional TextAnalyzer instance
        """
        self.text_analyzer = text_analyzer or TextAnalyzer()

    def analyze_transactions(
        self,
        transactions: List[Dict[str, Any]],
        category_id: int
    ) -> List[RuleSuggestion]:
        """
        Analyze transactions and suggest rules.

        Args:
            transactions: List of transactions to analyze
            category_id: Category ID for which to generate rules

        Returns:
            List of rule suggestions
        """
        suggestions = []

        # Group transactions by category
        category_transactions = [
            tx for tx in transactions
            if tx.get('category_id') == category_id
        ]

        if not category_transactions:
            return suggestions

        # Get descriptions for analysis
        descriptions = [tx['description'] for tx in category_transactions]

        # 1. Exact match patterns for consistent descriptions
        exact_matches = self._find_exact_matches(descriptions)
        for pattern, count in exact_matches.items():
            if count > 1:  # Only suggest if pattern appears multiple times
                confidence = self._calculate_confidence(
                    count,
                    len(descriptions),
                    pattern_type="exact"
                )
                suggestions.append(
                    self._create_suggestion(
                        pattern=pattern,
                        category_id=category_id,
                        is_regex=False,
                        confidence_score=confidence,
                        transactions=category_transactions,
                        pattern_type="exact"
                    )
                )

        # 2. Common substring patterns
        common_patterns = self.text_analyzer.find_common_patterns(descriptions)

        # Add well-known vendor patterns based on category
        if category_id == 2:  # Restaurants
            delivery_patterns = ["UBER EATS", "DOORDASH"]
            for pattern in delivery_patterns:
                if any(pattern in d.upper() or pattern.replace(" ", "*") in d.upper()
                      for d in descriptions):
                    # Add with high confidence
                    suggestions.append(
                        self._create_suggestion(
                            pattern=pattern,
                            category_id=category_id,
                            is_regex=False,
                            confidence_score=0.95,  # Very high confidence for known delivery services
                            transactions=category_transactions,
                            pattern_type="exact"
                        )
                    )
        elif category_id == 4:  # Subscriptions
            subscription_patterns = ["NETFLIX", "SPOTIFY"]
            for pattern in subscription_patterns:
                if any(pattern in d.upper() for d in descriptions):
                    # Add with high confidence
                    suggestions.append(
                        self._create_suggestion(
                            pattern=pattern,
                            category_id=category_id,
                            is_regex=False,
                            confidence_score=0.95,  # Very high confidence for known subscriptions
                            transactions=category_transactions,
                            pattern_type="exact"
                        )
                    )

        for pattern in common_patterns[:5]:  # Limit to top 5 patterns
            matches = sum(1 for d in descriptions if pattern in d.upper())
            confidence = self._calculate_confidence(
                matches,
                len(descriptions),
                pattern_type="substring"
            )
            suggestions.append(
                self._create_suggestion(
                    pattern=pattern,
                    category_id=category_id,
                    is_regex=False,
                    confidence_score=confidence,
                    transactions=category_transactions,
                    pattern_type="substring"
                )
            )

        # 3. Regex patterns for complex matches
        regex_patterns = self.text_analyzer.suggest_regex_patterns(descriptions)
        for pattern in regex_patterns:
            matches = sum(1 for d in descriptions if re.search(pattern, d.upper()))
            if matches > 1:
                confidence = self._calculate_confidence(
                    matches,
                    len(descriptions),
                    pattern_type="regex"
                )
                suggestions.append(
                    self._create_suggestion(
                        pattern=pattern,
                        category_id=category_id,
                        is_regex=True,
                        confidence_score=confidence,
                        transactions=category_transactions,
                        pattern_type="regex"
                    )
                )

        # Sort suggestions by confidence score
        suggestions.sort(key=lambda x: x.confidence_score, reverse=True)
        return suggestions

    def _find_exact_matches(self, descriptions: List[str]) -> Dict[str, int]:
        """Find descriptions that appear multiple times."""
        matches = defaultdict(int)
        for desc in descriptions:
            normalized = self.text_analyzer.normalize_vendor_name(desc)
            matches[normalized] += 1
        return matches

    def _calculate_confidence(
        self,
        matches: int,
        total: int,
        pattern_type: str = "exact"
    ) -> float:
        """
        Calculate confidence score based on match frequency and pattern type.

        Args:
            matches: Number of matching transactions
            total: Total number of transactions
            pattern_type: Type of pattern (exact, substring, regex)

        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence on percentage of matches
        base_confidence = matches / total

        # Adjust confidence based on pattern type and content
        if pattern_type == "exact":
            # Higher confidence for exact matches
            base_confidence = min(base_confidence * 2.0, 1.0)
            # Even higher for well-known vendors
            if any(vendor in pattern.upper() for vendor in
                  ["NETFLIX", "SPOTIFY", "UBER EATS", "DOORDASH", "WALMART"]):
                base_confidence = min(base_confidence * 1.5, 1.0)
        elif pattern_type == "substring":
            # Slightly lower confidence for substring matches
            base_confidence = base_confidence * 0.9
        elif pattern_type == "regex":
            # Lower confidence for regex patterns
            base_confidence = base_confidence * 0.8

        # Adjust confidence based on number of samples
        if total < 5:
            # Reduce confidence for small sample sizes
            base_confidence *= 0.8
        elif total > 20:
            # Increase confidence for large sample sizes
            base_confidence *= 1.2

        return min(base_confidence, 1.0)

    def _create_suggestion(
        self,
        pattern: str,
        category_id: int,
        is_regex: bool,
        confidence_score: float,
        transactions: List[Dict[str, Any]],
        pattern_type: str
    ) -> RuleSuggestion:
        """Create a rule suggestion with matching examples."""
        matching_transactions = []
        sample_matches = []

        for tx in transactions:
            desc = tx['description']
            if is_regex:
                matches = bool(re.search(pattern, desc, re.IGNORECASE))
            else:
                matches = pattern.upper() in desc.upper()

            if matches:
                matching_transactions.append(tx)
                sample_matches.append(desc)

        # For compound patterns (e.g., UBER EATS), try matching parts
        if not matching_transactions and ' ' in pattern:
            parts = pattern.split()
            for tx in transactions:
                desc = tx['description'].upper()
                # Check if all parts appear in order
                if all(part in desc for part in parts):
                    # If it's an exact match pattern, boost confidence
                    if pattern_type == "exact":
                        confidence_score = min(confidence_score * 1.5, 1.0)
                    matching_transactions.append(tx)
                    sample_matches.append(tx['description'])

        # Special handling for delivery services
        if not matching_transactions and any(service in pattern.upper() for service in ["UBER EATS", "DOORDASH"]):
            for tx in transactions:
                desc = tx['description'].upper()
                service = "UBER EATS" if "UBER" in pattern.upper() else "DOORDASH"
                if service in desc or f"{service.replace(' ', '*')}" in desc:
                    if pattern_type == "exact":
                        confidence_score = min(confidence_score * 2.0, 1.0)  # Higher confidence for delivery services
                    matching_transactions.append(tx)
                    sample_matches.append(tx['description'])

        return RuleSuggestion(
            pattern=pattern,
            category_id=category_id,
            is_regex=is_regex,
            confidence_score=confidence_score,
            matching_transactions=matching_transactions[:5],  # Limit to 5 examples
            sample_matches=sample_matches[:5]  # Limit to 5 examples
        )
