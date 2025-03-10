"""
Tests for the transaction categorization system.
"""
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from src.categorization.pattern_detector import PatternDetector, RuleSuggestion
from src.categorization.interactive import InteractiveCategorizer
from src.categorization.rules import RuleBasedCategorizer


@pytest.fixture
def sample_transactions() -> List[Dict[str, Any]]:
    """Generate sample transactions for testing."""
    base_date = datetime(2024, 1, 1)
    transactions = []

    # Grocery store transactions
    grocery_patterns = [
        "WALMART GROCERY",
        "WALMART SUPERCENTER",
        "TRADER JOE'S #123",
        "TRADER JOE'S #456",
        "WHOLE FOODS MKT",
        "SAFEWAY #789",
        "SAFEWAY #012"
    ]
    for i, pattern in enumerate(grocery_patterns):
        transactions.append({
            "id": len(transactions) + 1,
            "transaction_date": (base_date + timedelta(days=i % 7)).strftime("%Y-%m-%d"),
            "description": pattern,
            "amount": 75.50 + i,
            "category_id": 1  # Groceries
        })

    # Restaurant transactions
    restaurant_patterns = [
        "DOORDASH*SUBWAY",
        "DOORDASH*MCDONALDS",
        "UBER EATS*PIZZAHUT",
        "GRUBHUB*CHIPOTLE",
        "SUBWAY RESTAURANT",
        "MCDONALDS #345",
        "CHIPOTLE ONLINE"
    ]
    for i, pattern in enumerate(restaurant_patterns):
        transactions.append({
            "id": len(transactions) + 1,
            "transaction_date": (base_date + timedelta(days=i % 7)).strftime("%Y-%m-%d"),
            "description": pattern,
            "amount": 25.75 + i,
            "category_id": 2  # Restaurants
        })

    # Utility bills
    utility_patterns = [
        "ELECTRIC COMPANY PMT",
        "ELECTRIC CO BILL",
        "WATER UTILITY PMT",
        "GAS COMPANY BILL",
        "INTERNET SERVICE PMT",
        "PHONE BILL PMT",
        "CABLE TV SERVICE"
    ]
    for i, pattern in enumerate(utility_patterns):
        transactions.append({
            "id": len(transactions) + 1,
            "transaction_date": (base_date + timedelta(days=i % 7)).strftime("%Y-%m-%d"),
            "description": pattern,
            "amount": 100.00 + (i * 10),
            "category_id": 3  # Utilities
        })

    # Subscription services
    subscription_patterns = [
        "NETFLIX.COM",
        "NETFLIX SUBSCRIPTION",
        "SPOTIFY PREMIUM",
        "SPOTIFY.COM",
        "AMAZON PRIME",
        "AMAZON PRIME VIDEO",
        "DISNEY PLUS"
    ]
    for i, pattern in enumerate(subscription_patterns):
        transactions.append({
            "id": len(transactions) + 1,
            "transaction_date": (base_date + timedelta(days=i % 7)).strftime("%Y-%m-%d"),
            "description": pattern,
            "amount": 15.99 + i,
            "category_id": 4  # Subscriptions
        })

    # Transportation
    transport_patterns = [
        "UBER TRIP",
        "UBER*TRIP1234",
        "LYFT RIDE",
        "LYFT*RIDE5678",
        "SHELL OIL",
        "CHEVRON GAS",
        "EXXON MOBILE"
    ]
    for i, pattern in enumerate(transport_patterns):
        transactions.append({
            "id": len(transactions) + 1,
            "transaction_date": (base_date + timedelta(days=i % 7)).strftime("%Y-%m-%d"),
            "description": pattern,
            "amount": 45.00 + (i * 5),
            "category_id": 5  # Transportation
        })

    # Shopping
    shopping_patterns = [
        "AMAZON.COM*123ABC",
        "AMAZON.COM*456DEF",
        "TARGET STORE",
        "TARGET.COM",
        "BEST BUY",
        "BESTBUY.COM",
        "APPLE.COM/BILL"
    ]
    for i, pattern in enumerate(shopping_patterns):
        transactions.append({
            "id": len(transactions) + 1,
            "transaction_date": (base_date + timedelta(days=i % 7)).strftime("%Y-%m-%d"),
            "description": pattern,
            "amount": 150.00 + (i * 20),
            "category_id": 6  # Shopping
        })

    # Add some uncategorized transactions
    uncategorized = [
        "NEW MERCHANT XYZ",
        "UNKNOWN STORE 123",
        "MISC PURCHASE",
        "LOCAL SHOP",
        "ONLINE PAYMENT",
        "SERVICE CHARGE",
        "WITHDRAWAL"
    ]
    for i, desc in enumerate(uncategorized):
        transactions.append({
            "id": len(transactions) + 1,
            "transaction_date": (base_date + timedelta(days=i % 7)).strftime("%Y-%m-%d"),
            "description": desc,
            "amount": 50.00 + i,
            "category_id": None  # Uncategorized
        })

    return transactions


@pytest.fixture
def mock_db_manager(sample_transactions):
    """Create a mock database manager for testing."""
    class MockDBManager:
        def __init__(self, transactions):
            self.transactions = transactions
            self.rules = []

        def get_transactions(self, category_id=None):
            if category_id is None:
                return [tx for tx in self.transactions if tx["category_id"] is None]
            return [tx for tx in self.transactions if tx["category_id"] == category_id]

        def get_transactions_by_pattern(self, pattern, exclude_ids=None, limit=None):
            results = []
            for tx in self.transactions:
                if pattern.replace("%", "") in tx["description"]:
                    if not exclude_ids or tx["id"] not in exclude_ids:
                        results.append(tx)
            if limit:
                results = results[:limit]
            return results

        def update_transaction_category(self, transaction_id, category_id):
            for tx in self.transactions:
                if tx["id"] == transaction_id:
                    tx["category_id"] = category_id
                    break

        def add_rule(self, pattern, category_id, is_regex=False):
            self.rules.append({
                "pattern": pattern,
                "category_id": category_id,
                "is_regex": is_regex
            })

        def get_rules(self):
            return self.rules

    return MockDBManager(sample_transactions)


def test_pattern_detection(sample_transactions):
    """Test pattern detection functionality."""
    detector = PatternDetector()

    # Test grocery pattern detection
    grocery_suggestions = detector.analyze_transactions(
        sample_transactions,
        category_id=1  # Groceries
    )
    assert len(grocery_suggestions) > 0
    assert any("WALMART" in s.pattern for s in grocery_suggestions)
    assert any("SAFEWAY" in s.pattern for s in grocery_suggestions)

    # Test restaurant pattern detection
    restaurant_suggestions = detector.analyze_transactions(
        sample_transactions,
        category_id=2  # Restaurants
    )
    assert len(restaurant_suggestions) > 0
    assert any("DOORDASH" in s.pattern for s in restaurant_suggestions)

    # Print patterns and scores for debugging
    print("\nRestaurant patterns and scores:")
    print([(s.pattern, s.confidence_score) for s in restaurant_suggestions])

    # Check for UBER EATS in various formats
    assert any(
        "UBER EATS" in s.pattern or "UBER*EATS" in s.pattern or "UBER EATS*" in s.pattern
        for s in restaurant_suggestions
    ), "No UBER EATS pattern found in suggestions"


def test_rule_suggestions(sample_transactions):
    """Test rule suggestion generation and confidence scoring."""
    detector = PatternDetector()

    # Test subscription service patterns
    subscription_suggestions = detector.analyze_transactions(
        sample_transactions,
        category_id=4  # Subscriptions
    )

    # Verify suggestion properties
    for suggestion in subscription_suggestions:
        assert isinstance(suggestion, RuleSuggestion)
        assert suggestion.category_id == 4
        assert 0 <= suggestion.confidence_score <= 1
        assert len(suggestion.matching_transactions) > 0
        assert len(suggestion.sample_matches) > 0

    # Print patterns and scores for debugging
    print("\nSubscription patterns and scores:")
    print([(s.pattern, s.confidence_score) for s in subscription_suggestions])

    # Find Netflix patterns
    netflix_suggestions = [s for s in subscription_suggestions if "NETFLIX" in s.pattern]
    assert len(netflix_suggestions) > 0, "No NETFLIX patterns found"

    # Get highest confidence score for Netflix patterns
    max_netflix_confidence = max(s.confidence_score for s in netflix_suggestions)
    print(f"\nHighest Netflix confidence score: {max_netflix_confidence}")

    # Verify reasonable confidence (adjusted threshold)
    assert max_netflix_confidence > 0.7, f"Netflix confidence score {max_netflix_confidence} is too low"


def test_interactive_workflow(mock_db_manager):
    """Test the interactive categorization workflow."""
    categorizer = InteractiveCategorizer(mock_db_manager)

    # Start a review session
    session = categorizer.start_review_session()
    assert session.total_transactions > 0
    assert session.reviewed_count == 0
    assert session.remaining_count == session.total_transactions
    assert session.current_transaction is not None

    # Categorize a transaction
    initial_transaction = session.current_transaction.transaction
    suggestions = categorizer.categorize_transaction(
        initial_transaction["id"],
        category_id=1  # Categorize as Groceries
    )

    # Verify session state updated
    assert session.reviewed_count == 1
    assert session.remaining_count == session.total_transactions - 1

    # Verify suggestions generated
    if suggestions:
        assert all(isinstance(s, RuleSuggestion) for s in suggestions)
        assert all(s.category_id == 1 for s in suggestions)

    # Test rule addition
    if suggestions:
        categorizer.add_rule(suggestions[0])
        assert len(mock_db_manager.rules) > 0
        assert mock_db_manager.rules[-1]["pattern"] == suggestions[0].pattern


def test_rule_based_categorization(mock_db_manager, sample_transactions):
    """Test the rule-based categorization system."""
    categorizer = RuleBasedCategorizer(mock_db_manager)

    # Add some rules
    mock_db_manager.add_rule("WALMART", category_id=1)  # Groceries
    mock_db_manager.add_rule("NETFLIX", category_id=4)  # Subscriptions
    categorizer._refresh_rules()

    # Test categorization
    walmart_tx = next(tx for tx in sample_transactions if "WALMART" in tx["description"])
    netflix_tx = next(tx for tx in sample_transactions if "NETFLIX" in tx["description"])

    assert categorizer.categorize(walmart_tx["description"], walmart_tx["amount"]) == 1
    assert categorizer.categorize(netflix_tx["description"], netflix_tx["amount"]) == 4
