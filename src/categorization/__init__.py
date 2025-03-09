"""
Transaction categorization module.

This module provides functionality for automatically categorizing
financial transactions using a combination of rule-based matching
and optional machine learning approaches.

Main Components:
- TransactionCategorizer: Main entry point that combines all approaches
- RuleBasedCategorizer: Rule-based categorization
- MLCategorizer: Machine learning based categorization
- TextAnalyzer: Text analysis utilities
"""
from .categorizer import TransactionCategorizer
from .rules import RuleBasedCategorizer, CategorizationRule
from .ml import MLCategorizer
from .text import TextAnalyzer

__all__ = [
    "TransactionCategorizer",
    "RuleBasedCategorizer",
    "CategorizationRule",
    "MLCategorizer",
    "TextAnalyzer"
]
