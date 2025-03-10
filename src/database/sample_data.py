"""
Sample data generation for testing the categorization system.
"""
import sqlite3
import random
import re
from datetime import datetime, timedelta
from pathlib import Path

# Categories with hierarchy
CATEGORIES = {
    "Essential": [
        "Groceries",
        "Healthcare",
        "Utilities"
    ],
    "Food & Dining": [
        "Restaurants",
        "Fast Food",
        "Coffee Shops"
    ],
    "Transportation": [
        "Public Transit",
        "Ride Share",
        "Gas & Fuel"
    ],
    "Shopping": [
        "Online Shopping",
        "Department Stores",
        "Electronics"
    ],
    "Entertainment": [
        "Movies & Shows",
        "Games",
        "Music"
    ]
}

# Sample merchants with realistic patterns
MERCHANTS = {
    "Groceries": [
        "WALMART GROCERY #123",
        "WALMART SUPERCENTER",
        "TRADER JOE'S #456",
        "TRADER JOES",  # Intentionally different format
        "WHOLE FOODS MKT",
        "SAFEWAY #789",
        "KROGER FOOD #012"
    ],
    "Healthcare": [
        "CVS PHARMACY #1234",
        "WALGREENS RX #567",
        "QUEST DIAGNOSTICS",
        "LABCORP TESTING",
        "MINUTE CLINIC VISIT"
    ],
    "Utilities": [
        "ELECTRIC COMPANY PMT",
        "WATER UTILITY PMT",
        "GAS COMPANY BILL",
        "INTERNET SERVICE PMT",
        "PHONE BILL PMT"
    ],
    "Restaurants": [
        "DOORDASH*SUBWAY",
        "DOORDASH*MCDONALDS",
        "UBER EATS*PIZZAHUT",
        "GRUBHUB*CHIPOTLE",
        "RESTAURANT PMT"
    ],
    "Fast Food": [
        "MCDONALDS #345",
        "SUBWAY #678",
        "CHIPOTLE ONLINE",
        "BURGER KING #901",
        "WENDYS #234"
    ],
    "Coffee Shops": [
        "STARBUCKS #567",
        "PEETS COFFEE #890",
        "DUNKIN #123",
        "LOCAL COFFEE",
        "COFFEE BEAN #456"
    ],
    "Public Transit": [
        "METRO TRANSIT PMT",
        "BUS PASS RENEWAL",
        "TRAIN TICKET",
        "SUBWAY TICKET",
        "TRANSIT CARD RELOAD"
    ],
    "Ride Share": [
        "UBER*TRIP1234",
        "UBER*RIDE5678",
        "LYFT*RIDE9012",
        "LYFT*TRIP3456",
        "TAXI SERVICE"
    ],
    "Gas & Fuel": [
        "SHELL OIL #123",
        "CHEVRON #456",
        "EXXON #789",
        "MOBIL #012",
        "GAS STATION"
    ],
    "Online Shopping": [
        "AMAZON.COM*123ABC",
        "AMAZON.COM*456DEF",
        "EBAY*ITEM789",
        "ETSY*PURCHASE012",
        "PAYPAL*MERCHANT"
    ],
    "Department Stores": [
        "TARGET #123",
        "TARGET.COM",
        "KOHLS #456",
        "MACYS #789",
        "NORDSTROM"
    ],
    "Electronics": [
        "BESTBUY.COM",
        "APPLE.COM/BILL",
        "NEWEGG.COM",
        "MICROCENTER",
        "ELECTRONICS STORE"
    ],
    "Movies & Shows": [
        "NETFLIX.COM",
        "HULU*SUBSCRIPTION",
        "AMC THEATERS #123",
        "REGAL CINEMA",
        "DISNEY+"
    ],
    "Games": [
        "STEAM GAMES",
        "NINTENDO ESHOP",
        "PLAYSTATION NETWORK",
        "XBOX LIVE",
        "GAME STORE"
    ],
    "Music": [
        "SPOTIFY.COM",
        "APPLE MUSIC",
        "PANDORA",
        "CONCERT TICKETS",
        "MUSIC STORE"
    ]
}

# Initial categorization rules
RULES = [
    # High confidence rules (exact matches)
    {"pattern": "WALMART", "category": "Groceries", "is_regex": False, "priority": 100},
    {"pattern": "TRADER JOE'?S", "category": "Groceries", "is_regex": True, "priority": 100},
    {"pattern": "WHOLE FOODS", "category": "Groceries", "is_regex": False, "priority": 100},

    # Delivery service patterns
    {"pattern": r"DOORDASH\*", "category": "Restaurants", "is_regex": True, "priority": 90},
    {"pattern": r"UBER EATS\*", "category": "Restaurants", "is_regex": True, "priority": 90},
    {"pattern": r"GRUBHUB\*", "category": "Restaurants", "is_regex": True, "priority": 90},

    # Transportation patterns
    {"pattern": r"UBER\*TRIP|UBER\*RIDE", "category": "Ride Share", "is_regex": True, "priority": 85},
    {"pattern": r"LYFT\*", "category": "Ride Share", "is_regex": True, "priority": 85},

    # Subscription services
    {"pattern": "NETFLIX", "category": "Movies & Shows", "is_regex": False, "priority": 95},
    {"pattern": "SPOTIFY", "category": "Music", "is_regex": False, "priority": 95},
    {"pattern": "HULU", "category": "Movies & Shows", "is_regex": False, "priority": 95},

    # Shopping patterns
    {"pattern": r"AMAZON\.COM", "category": "Online Shopping", "is_regex": True, "priority": 80},
    {"pattern": "TARGET", "category": "Department Stores", "is_regex": False, "priority": 80},

    # Utility patterns
    {"pattern": r".*UTILITY PMT", "category": "Utilities", "is_regex": True, "priority": 75},
    {"pattern": r".*BILL PMT", "category": "Utilities", "is_regex": True, "priority": 75}
]

def create_sample_data(db_path: Path) -> None:
    """Create sample data for testing."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Insert top-level categories
    category_ids = {}
    for top_level, subcategories in CATEGORIES.items():
        cursor.execute(
            'INSERT INTO categories (name, parent_id) VALUES (?, NULL)',
            (top_level,)
        )
        parent_id = cursor.lastrowid
        category_ids[top_level] = parent_id

        # Insert subcategories
        for subcategory in subcategories:
            cursor.execute(
                'INSERT INTO categories (name, parent_id) VALUES (?, ?)',
                (subcategory, parent_id)
            )
            category_ids[subcategory] = cursor.lastrowid

    # Insert rules
    rule_ids = {}
    for rule in RULES:
        cursor.execute('''
            INSERT INTO categorization_rules (
                pattern,
                category_id,
                is_regex,
                priority
            ) VALUES (?, ?, ?, ?)
        ''', (
            rule['pattern'],
            category_ids[rule['category']],
            rule['is_regex'],
            rule['priority']
        ))
        rule_ids[rule['pattern']] = cursor.lastrowid

    # Generate transactions over the last 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)

    # Generate transactions for each category
    for category, merchants in MERCHANTS.items():
        # Number of transactions varies by category
        num_transactions = random.randint(5, 15)

        for _ in range(num_transactions):
            # Random date within the last 6 months
            transaction_date = start_date + timedelta(
                days=random.randint(0, 180)
            )

            # Select random merchant
            merchant = random.choice(merchants)

            # Generate amount based on category typical ranges
            if category in ['Groceries', 'Shopping']:
                amount = round(random.uniform(20, 200), 2)
            elif category in ['Coffee Shops', 'Fast Food']:
                amount = round(random.uniform(5, 30), 2)
            elif category in ['Utilities']:
                amount = round(random.uniform(50, 300), 2)
            else:
                amount = round(random.uniform(10, 100), 2)

            # Find matching rule
            matching_rule_id = None
            for pattern, rule_id in rule_ids.items():
                if pattern in merchant or (
                    pattern.startswith('r"') and
                    re.match(pattern[2:-1], merchant)
                ):
                    matching_rule_id = rule_id
                    break

            # 80% of transactions are categorized
            category_id = category_ids[category] if random.random() < 0.8 else None

            cursor.execute('''
                INSERT INTO transactions (
                    date,
                    description,
                    amount,
                    category_id,
                    rule_id
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                transaction_date.strftime('%Y-%m-%d'),
                merchant,
                amount,
                category_id,
                matching_rule_id
            ))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_sample_data(Path('data/transactions.db'))
