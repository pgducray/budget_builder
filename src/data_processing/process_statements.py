"""
Script to process MCB bank statements using the StatementLoader and store in SQLite.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from pandas import DataFrame

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_processing.loader import StatementLoader
from database import DatabaseManager  # DatabaseManager is now exported from __init__.py

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def prepare_transactions(df: DataFrame) -> List[Dict[str, Any]]:
    """
    Prepare transactions for database insertion.

    Args:
        df: DataFrame from loader

    Returns:
        List of transaction dictionaries ready for database
    """
    transactions = []

    for _, row in df.iterrows():
        # Skip rows without transaction date
        if pd.isna(row['TRANS\nDATE']):
            continue

        # Determine amount (positive for credit, negative for debit)
        amount = float(row['CREDIT']) if pd.notna(row['CREDIT']) else -float(row['DEBIT'])

        # Clean up transaction details (remove extra newlines)
        description = ' '.join(row['TRANSACTION DETAILS'].split())

        transaction = {
            'transaction_date': row['TRANS\nDATE'],
            'description': description,
            'amount': amount,
            'reference_number': row['transaction reference number'] if pd.notna(row['transaction reference number']) else None
        }

        transactions.append(transaction)

    return transactions


def process_statement(file_path: Path, loader: StatementLoader, db_manager: DatabaseManager) -> None:
    """
    Process a single MCB bank statement file and store in database.

    Args:
        file_path: Path to the statement file
        loader: StatementLoader instance
        db_manager: DatabaseManager instance

    Raises:
        ValueError: If the file cannot be loaded or processed
    """
    # Load and process the statement
    df = loader.load_statement(file_path)

    # Prepare transactions for database insertion
    transactions = prepare_transactions(df)

    # Add transactions to database (duplicates will be ignored due to UNIQUE constraints)
    db_manager.add_transactions(transactions)


def main() -> None:
    """Process all MCB bank statements in the raw directory and store in SQLite."""
    try:
        # Initialize components
        loader = StatementLoader()
        db_path = Path("data/finance.db")
        logger.info(f"Using database at: {db_path}")

        db_manager = DatabaseManager(db_path)
        logger.info("Created DatabaseManager")

        # Initialize database schema
        db_manager.initialize_database()
        logger.info("Initialized database schema")

        # Setup raw directory
        raw_dir = Path("data/raw")

        if not raw_dir.exists():
            logger.error(f"Raw directory not found: {raw_dir}")
            return

        # Process each PDF file
        for file_path in raw_dir.glob("*.pdf"):
            logger.info(f"Processing {file_path.name}...")

            try:
                # Process the statement and store in database
                process_statement(file_path, loader, db_manager)
                logger.info(f"Successfully processed and stored {file_path.name}")

            except ValueError as e:
                logger.error(f"Error processing {file_path.name}: {str(e)}")
            except Exception as e:
                logger.exception(f"Unexpected error processing {file_path.name}")

    except Exception as e:
        logger.exception("Unexpected error in main:")


if __name__ == "__main__":
    main()
