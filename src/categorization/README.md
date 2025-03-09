# Transaction Categorization System

This module provides a flexible system for automatically categorizing financial transactions based on their descriptions and other attributes.

## Features

- Rule-based categorization with priority levels
- Support for both exact string matching and regex patterns
- Vendor name normalization and text analysis
- Flexible rule management (add/remove/update)
- Configuration file support for easy rule management
- Batch processing capability
- Optional ML-based categorization for edge cases

## Category IDs

The example configuration uses the following category IDs:

1. Entertainment (Netflix, Spotify)
2. Shopping (Amazon)
3. Transportation (Uber, Lyft)
4. Groceries
5. Dining (Restaurants, Cafes)
6. Insurance
7. Housing (Rent, Mortgage)
8. Utilities (Water, Electric, Gas)

## Usage Examples

### Basic Usage

```python
from pathlib import Path
from database.db_manager import DatabaseManager
from categorization.categorizer import TransactionCategorizer

# Initialize database manager
db_manager = DatabaseManager(Path("data/finance.db"))

# Create categorizer
categorizer = TransactionCategorizer(db_manager)

# Categorize a single transaction
transaction = {
    "description": "NETFLIX MONTHLY SUB",
    "amount": 15.99,
    "vendor": "NETFLIX INC"
}

category_id = categorizer.categorize_transaction(
    description=transaction["description"],
    amount=transaction["amount"],
    vendor=transaction["vendor"]
)
# Returns category_id = 1 (Entertainment)
```

### Managing Rules

```python
# Add a new rule
categorizer.add_rule(
    pattern="HULU",
    category_id=1,  # Entertainment
    priority=100
)

# Add a regex rule
categorizer.add_rule(
    pattern="^WALMART",
    category_id=4,  # Groceries
    priority=85,
    is_regex=True
)

# Update an existing rule
categorizer.update_rule(
    rule_id=1,  # Rule ID from database
    priority=110  # Make rule highest priority
)

# Delete a rule
categorizer.delete_rule(rule_id=2)  # Rule ID from database

# Migrate rules from JSON config
categorizer = TransactionCategorizer.migrate_from_json(
    db_manager=db_manager,
    json_path="config/categorization_rules.json",
    clear_existing=True  # Optional: clear existing rules
)
```

### Batch Processing

```python
transactions = [
    {
        "description": "NETFLIX MONTHLY SUB",
        "amount": 15.99,
        "vendor": "NETFLIX INC"
    },
    {
        "description": "UBER TRIP 123",
        "amount": 25.50,
        "vendor": "UBER"
    }
]

categorized = categorizer.categorize_batch(transactions)
# Returns list of transactions with added category_ids
```

## Text Analysis

The system includes a TextAnalyzer class that helps improve categorization accuracy by:

1. Normalizing vendor names:
   - Removing common business suffixes (INC, LLC, etc.)
   - Converting to uppercase
   - Removing special characters

2. Extracting relevant keywords:
   - Filtering out common transaction-related words
   - Removing short words
   - Cleaning special characters

## ML Categorization (Optional)

The system includes a placeholder MLCategorizer class that can be implemented to:

1. Handle transactions that don't match any rules
2. Learn from historical categorizations
3. Provide confidence scores for predictions

## Best Practices

1. Order rules by specificity and priority:
   - More specific rules should have higher priority
   - Generic patterns should have lower priority

2. Use regex patterns for flexible matching:
   - `^AMZN` matches any Amazon transaction
   - `GROCERY|SUPERMARKET` matches various grocery stores

3. Regularly review and update rules:
   - Export rules to track changes
   - Remove outdated patterns
   - Adjust priorities based on accuracy

4. Test new rules before deployment:
   - Use batch processing to validate changes
   - Check for conflicts with existing rules
