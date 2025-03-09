# Personal Finance Tracker

A Python-based tool for analyzing bank statements, automating transaction categorization, and providing financial insights.

## Features

- **Automated Statement Processing**: Convert bank statements to structured data
- **Smart Transaction Categorization**:
  - Rule-based matching with priority levels
  - Text analysis and vendor normalization
  - Optional ML-based categorization
  - Database-backed rule storage
- **Financial Analysis**: Generate insights and visualizations
- **SQLite Database**: Efficient and reliable data storage

## Project Structure

```
budget_builder/
├── src/
│   ├── data_processing/   # Statement processing
│   │   ├── __init__.py
│   │   ├── loader.py      # Statement parsing
│   │   └── process_statements.py
│   │
│   ├── database/         # Database operations
│   │   ├── __init__.py   # Unified DatabaseManager
│   │   ├── base.py       # Base functionality
│   │   ├── transactions.py
│   │   ├── categories.py
│   │   └── rules.py
│   │
│   ├── categorization/   # Transaction categorization
│   │   ├── __init__.py   # Public interface
│   │   ├── categorizer.py # Main categorizer
│   │   ├── rules.py      # Rule-based logic
│   │   ├── text.py       # Text analysis
│   │   └── ml.py         # ML categorization
│   │
│   ├── analytics/        # Financial analysis
│   │   ├── __init__.py
│   │   └── analyzer.py
│   │
│   └── utils/           # Utility functions
│
├── tests/               # Test files mirroring src/
├── data/
│   ├── raw/            # Original bank statements
│   └── processed/      # Cleaned data
├── config/             # Configuration files
├── notebooks/          # Jupyter notebooks
├── docker/            # Docker configuration
├── requirements.txt    # Python dependencies
└── README.md
```

## Setup Instructions

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the database:
   ```python
   from pathlib import Path
   from database import DatabaseManager

   db = DatabaseManager(Path("data/finance.db"))
   db.initialize_database()
   ```

## Usage Examples

### Process Bank Statements

```python
from pathlib import Path
from data_processing.loader import StatementLoader
from database import DatabaseManager

# Initialize components
loader = StatementLoader()
db = DatabaseManager(Path("data/finance.db"))

# Process statements
for file_path in Path("data/raw").glob("*.pdf"):
    process_statement(file_path, loader, db)
```

### Transaction Categorization

```python
from categorization import TransactionCategorizer
from database import DatabaseManager

# Initialize components
db = DatabaseManager(Path("data/finance.db"))
categorizer = TransactionCategorizer(db)

# Add categorization rules
categorizer.add_rule(
    pattern="NETFLIX",
    category_id=1,  # Entertainment
    priority=100
)

# Categorize transactions
transactions = db.get_transactions()
categorized = categorizer.categorize_batch(transactions)
```

### Rule Management

```python
# Import rules from JSON
categorizer = TransactionCategorizer.migrate_from_json(
    db_manager=db,
    json_path="config/categorization_rules.json",
    clear_existing=True
)

# Add new rules
db.add_rule(
    pattern="^AMZN",
    category_id=2,  # Shopping
    priority=90,
    is_regex=True
)
```

## Development Workflow

1. Data Processing:
   - Place bank statements in `data/raw/`
   - Run `process_statements.py`
   - Data is stored in SQLite database

2. Transaction Categorization:
   - Define rules in database or import from JSON
   - Process transactions using rules
   - Optionally train ML model for edge cases

3. Analysis:
   - Generate insights and visualizations
   - Export reports as needed

## Testing

Run tests using pytest:
```bash
pytest tests/
```

## Docker Support

Build and run using Docker:
```bash
docker build -t finance-tracker .
docker run finance-tracker
```

## Architecture

The system uses a modular architecture with clear separation of concerns:

1. **Database Layer** (`src/database/`):
   - Handles all data persistence
   - ACID compliant with SQLite
   - Separate managers for different entities

2. **Categorization Engine** (`src/categorization/`):
   - Rule-based matching with priorities
   - Text analysis and normalization
   - Optional ML-based categorization
   - Clean interface through TransactionCategorizer

3. **Data Processing** (`src/data_processing/`):
   - Statement parsing and normalization
   - Data cleaning and validation
   - Direct database integration

4. **Analytics** (`src/analytics/`):
   - Financial analysis and insights
   - Visualization capabilities
   - Budget tracking and recommendations
