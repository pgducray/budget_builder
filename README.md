# Budget Builder

A Python tool to process bank transactions and categorize them based on patterns.

## Features

- PDF bank statement processing (MCB bank statements)
- Robust transaction extraction with duplicate detection
- Unified transaction database in CSV format
- Pattern-based transaction categorization
- Transaction summary by category

## Project Structure

```
budget_builder/
├── config/
│   ├── categorization_rules.json  # Transaction categorization rules
│   └── default_config.json       # Default configuration
├── data/
│   ├── raw/          # Place new PDF bank statements here
│   ├── processed/    # Processed PDFs are moved here
│   ├── transactions.csv        # Unified transaction database
│   └── categorized_transactions.csv  # Final categorized output
└── src/
    ├── data_processing/
    │   ├── extract_data.py     # PDF data extraction
    │   └── process_all_statements.py  # Process PDFs & maintain database
    ├── categorization/
    │   └── simple_categorizer.py  # Transaction categorizer
    └── categorize_transactions.py # Main categorization script
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

You can also run just the processing step without categorization using:
```bash
make process
```

## Categorization Rules

Transactions are categorized based on:
1. Transaction type patterns (e.g., "Salary" → Income)
2. Merchant name patterns (e.g., "COFFEE" → Coffee Shops)
3. Default fallback to "Uncategorized"

Current categories include:
- Income
- Coffee Shops
- Restaurants
- Groceries
- Shopping
- Cash Withdrawal
- Transfer
- Uncategorized

You can customize the categorization rules by modifying `config/categorization_rules.json`.
