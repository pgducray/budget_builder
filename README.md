# Budget Builder

A Python tool to process bank transactions and categorize them based on patterns, with a Streamlit GUI for analysis and visualization.

## Features

- PDF bank statement processing (MCB bank statements)
- Robust transaction extraction with duplicate detection
- Unified transaction database in CSV format
- Pattern-based transaction categorization using regex patterns
- Interactive Streamlit GUI for analysis and budget review
- Jupyter notebook workflow for pattern optimization
- Transaction summary by category

## Project Structure

```
budget_builder/
├── data/
│   ├── raw/                    # Place new PDF bank statements here
│   ├── processed/              # Processed PDFs are moved here
│   ├── transactions.csv        # Unified transaction database
│   ├── categorized_transactions.csv  # Final categorized output
│   └── patterns.json           # Regex patterns for categorization
├── pages/
│   ├── 1_Analysis.py          # Transaction analysis page
│   ├── 2_Pattern_Management.py # Pattern management interface
│   └── 3_Budget_Review.py     # Budget review and insights
├── src/
│   ├── categorization/
│   │   ├── __init__.py
│   │   └── simple_categorizer.py    # Transaction categorizer
│   ├── data_processing/
│   │   ├── __init__.py
│   │   ├── extract_data.py          # PDF data extraction
│   │   └── process_all_statements.py # Process PDFs & maintain database
│   ├── shared/
│   │   └── components.py            # Shared UI components
│   ├── analysis.py                  # Analysis functions
│   ├── categorize_transactions.py   # Main categorization script
│   ├── config.py                    # Configuration settings
│   ├── refine_patterns.py          # Pattern refinement utilities
│   └── utils.py                     # Utility functions
└── gui.py                          # Main Streamlit application
```

## Setup

1. Create a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create required directories:
```bash
make setup
```

## Usage

### Available Make Commands

The project includes a Makefile for common operations:

- `make setup` - Create required directories
- `make process` - Process all statements in data/raw
- `make categorize` - Process statements and categorize transactions
- `make clean` - Remove processed files
- `make validate` - Check if required directories exist
- `make help` - Show available commands

### Processing and Categorizing Transactions

1. Place your MCB bank statement PDF files in the `data/raw` directory
2. Run the processor and categorizer:
```bash
make categorize
```

This will:
- Validate required directories exist
- Extract transactions from PDFs in data/raw
- Move processed PDFs to data/processed
- Update the unified transactions.csv database
- Remove any duplicates
- Categorize all transactions based on patterns
- Generate a category summary
- Save categorized transactions to data/categorized_transactions.csv

### Using the Streamlit Interface

Launch the Streamlit application:
```bash
streamlit run gui.py
```

The interface provides:
1. Transaction Analysis - View and analyze your transaction history
2. Pattern Management - Manage categorization patterns
3. Budget Review - Review your spending patterns and budget

### Pattern Optimization Workflow

The project uses a pattern-based approach for transaction categorization, with patterns stored in `data/patterns.json`. To optimize categorization:

1. Open the category optimization notebook:
```bash
jupyter notebook notebooks/category_optimization.ipynb
```

2. Review uncategorized transactions and identify patterns
3. Edit patterns.json directly to add or refine regex patterns
4. Re-run categorization to verify improvements

## Current Categories

The following categories are defined in `patterns.json`:
- Income
- Groceries
- Coffee Shops
- Car Transaction
- Transportation & Fuel
- Servicing and Car Insurance
- Sport
- Utilities
- Insurance
- Healthcare
- Bank Charges
- Taxes
- Home and Appliances
- Internal Transfert
- Cash
- Family
- Other
- Entertainment
- Subscription
- Gift
- Restaurants

Each category has associated regex patterns in `patterns.json` that match against transaction descriptions. Any transaction not matching these patterns remains uncategorized.
