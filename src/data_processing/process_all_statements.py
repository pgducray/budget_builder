"""
Process all bank statements in the data/raw directory and create a master CSV file.
"""

import logging
from pathlib import Path
import pandas as pd
import shutil
from typing import List, Optional
from dataclasses import dataclass

from src.data_processing.extract_data import (
    extract_transactions,
    format_transactions,
    StatementProcessingError,
    NoTransactionTablesError,
    InvalidTransactionDataError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingConfig:
    """Configuration for statement processing"""
    raw_dir: Path
    processed_dir: Path
    output_file: Path

    @classmethod
    def default(cls) -> 'ProcessingConfig':
        """Create default configuration"""
        return cls(
            raw_dir=Path('data/raw'),
            processed_dir=Path('data/processed'),
            output_file=Path('data/transactions.csv')
        )

    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

def _is_already_processed(pdf_file: Path, processed_dir: Path) -> bool:
    """
    Check if PDF was already processed by checking filename.

    Args:
        pdf_file: PDF file to check
        processed_dir: Directory containing processed PDFs

    Returns:
        True if PDF was already processed, False otherwise
    """
    return (processed_dir / pdf_file.name).exists()

def _get_existing_transactions(output_file: Path) -> pd.DataFrame:
    """
    Load existing transactions or return empty DataFrame.

    Args:
        output_file: Path to the transactions CSV file

    Returns:
        DataFrame containing existing transactions or empty DataFrame with correct columns
    """
    if output_file.exists():
        try:
            return pd.read_csv(output_file)
        except Exception as e:
            logger.error(f"Error reading existing transactions: {e}")
            return pd.DataFrame(columns=['transaction_date', 'description', 'amount', 'reference_number'])
    return pd.DataFrame(columns=['transaction_date', 'description', 'amount', 'reference_number'])

def _filter_new_transactions(new_df: pd.DataFrame, existing_df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate transactions.

    Args:
        new_df: DataFrame containing new transactions
        existing_df: DataFrame containing existing transactions

    Returns:
        DataFrame containing only new transactions
    """
    if existing_df.empty:
        return new_df

    # Create copies and ensure amount is float
    new_df = new_df.copy()
    existing_df = existing_df.copy()

    # Convert amounts to float
    new_df['amount'] = pd.to_numeric(new_df['amount'], errors='coerce')
    existing_df['amount'] = pd.to_numeric(existing_df['amount'], errors='coerce')

    # First try matching by reference number if available
    unique_transactions = []

    # For rows with reference numbers, use reference matching
    mask_with_ref = new_df['reference_number'].notna()
    if mask_with_ref.any():
        refs = new_df.loc[mask_with_ref]
        unique_transactions.append(
            refs[~refs['reference_number'].isin(existing_df['reference_number'])]
        )

    # For rows without reference numbers, use all columns matching
    mask_without_ref = ~mask_with_ref
    if mask_without_ref.any():
        no_refs = new_df.loc[mask_without_ref]
        merge_cols = ['transaction_date', 'description', 'amount']
        merged = no_refs.merge(
            existing_df[merge_cols],
            how='left',
            indicator=True
        )
        unique_transactions.append(
            no_refs[no_refs.index.isin(
                merged[merged['_merge'] == 'left_only'].index
            )]
        )

    result = pd.concat(unique_transactions, ignore_index=True) if unique_transactions else pd.DataFrame(columns=new_df.columns)

    filtered_count = len(new_df) - len(result)
    if filtered_count > 0:
        logger.info(f"Filtered out {filtered_count} duplicate transactions")

    return result

def process_statement(pdf_file: Path, config: ProcessingConfig, existing_transactions: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Process a single PDF statement file.

    Args:
        pdf_file: Path to the PDF file to process
        config: Processing configuration
        existing_transactions: DataFrame of existing transactions

    Returns:
        DataFrame of new transactions if successful, None if processing failed
    """
    try:
        # Extract and format transactions
        logger.info(f"Processing {pdf_file.name}")
        raw_df = extract_transactions(pdf_file)
        formatted_df = format_transactions(raw_df)

        # Filter out duplicate transactions
        unique_df = _filter_new_transactions(formatted_df, existing_transactions)

        if unique_df.empty:
            logger.info(f"No new transactions found in {pdf_file.name}")
            return None

        # Move PDF to processed directory
        dest_path = config.processed_dir / pdf_file.name
        shutil.move(str(pdf_file), str(dest_path))
        logger.info(f"Moved {pdf_file.name} to {config.processed_dir}")

        return unique_df

    except (StatementProcessingError, NoTransactionTablesError, InvalidTransactionDataError) as e:
        logger.error(f"Failed to process {pdf_file.name}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing {pdf_file.name}: {str(e)}")
        return None

def process_all_statements(config: Optional[ProcessingConfig] = None) -> None:
    """
    Process all PDF statements in raw_dir, move them to processed_dir, and update the master CSV.
    Handles duplicate detection both by PDF filename and transaction reference numbers.

    Args:
        config: Processing configuration (optional, uses default if not provided)
    """
    # Use default config if not provided
    config = config or ProcessingConfig.default()
    config.ensure_directories()

    # Load existing transactions
    existing_transactions = _get_existing_transactions(config.output_file)
    if not existing_transactions.empty:
        logger.info(f"Loaded {len(existing_transactions)} existing transactions")

    # Find all PDF files
    pdf_files = list(config.raw_dir.glob('*.pdf'))
    if not pdf_files:
        logger.warning(f"No PDF files found in {config.raw_dir}")
        return

    logger.info(f"Found {len(pdf_files)} PDF files to process")

    # Process each unprocessed PDF
    new_transactions = []
    for pdf_file in pdf_files:
        if _is_already_processed(pdf_file, config.processed_dir):
            logger.info(f"Skipping {pdf_file.name} - already processed")
            continue

        result_df = process_statement(pdf_file, config, existing_transactions)
        if result_df is not None:
            new_transactions.append(result_df)

    # Update master CSV if we have new transactions
    if new_transactions:
        try:
            # Combine new transactions
            new_df = pd.concat(new_transactions, ignore_index=True)
            logger.info(f"Found {len(new_df)} new transactions")

            # Combine with existing transactions and save
            final_df = (
                new_df if existing_transactions.empty
                else pd.concat([existing_transactions, new_df], ignore_index=True)
            )

            final_df.to_csv(config.output_file, index=False)
            logger.info(f"Updated {config.output_file} - now contains {len(final_df)} transactions")
        except Exception as e:
            logger.error(f"Failed to update master CSV: {str(e)}")
    else:
        logger.info("No new transactions to add")

if __name__ == '__main__':
    process_all_statements()
