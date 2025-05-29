"""
Module for extracting bank statement transaction data.
Specifically designed for MCB bank statements in PDF format.
"""

from typing import Optional, Tuple, List
import re
import pandas as pd
from pathlib import Path
import camelot
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StatementProcessingError(Exception):
    """Base exception for statement processing errors"""
    pass

class NoTransactionTablesError(StatementProcessingError):
    """Raised when no transaction tables are found"""
    pass

class InvalidTransactionDataError(StatementProcessingError):
    """Raised when transaction data is invalid"""
    pass

# Constants for pattern matching
TRANSACTION_HEADERS = [
    ['TRANS\nDATE', 'VALUE\nDATE', 'TRANSACTION DETAILS', 'DEBIT', 'CREDIT', 'BALANCE'],
    ['TRANS\nDATE', 'VALUE\nDATE', 'TRANSACTION DETAILS', 'DEBIT', 'CREDIT', 'DEBIT', 'CREDIT', 'BALANCE\n(-) Indicates a debit'],
    ['TRANS\nDATE', 'VALUE\nDATE', 'TRANSACTION DETAILS', 'DEBIT', 'CREDIT', 'DEBIT', 'CREDIT', 'BALANCE']
]
REFERENCE_PATTERN = re.compile(r'(FT\d+[A-Z0-9]+\\BNK)')

def validate_transaction_data(df: pd.DataFrame) -> None:
    """
    Validate extracted transaction data.

    Args:
        df: DataFrame to validate

    Raises:
        InvalidTransactionDataError: If data validation fails
    """
    required_cols = {'transaction_date', 'description', 'amount'}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise InvalidTransactionDataError(f"Missing required columns: {missing_cols}")

    # Validate data types and values
    try:
        # Check dates - specify dayfirst=True for dd/mm/yyyy format
        if not pd.to_datetime(df['transaction_date'], dayfirst=True, errors='coerce').notna().all():
            raise InvalidTransactionDataError("Invalid transaction dates found")

        # Clean and check amounts - remove any currency symbols and commas
        df['amount'] = df['amount'].astype(str).str.replace('Rs', '', regex=False)
        df['amount'] = df['amount'].str.replace(',', '', regex=False)
        df['amount'] = df['amount'].str.strip()
        if not pd.to_numeric(df['amount'], errors='coerce').notna().all():
            raise InvalidTransactionDataError("Invalid transaction amounts found")

        # Check descriptions
        if df['description'].isna().any() or (df['description'] == '').any():
            raise InvalidTransactionDataError("Empty transaction descriptions found")

    except Exception as e:
        raise InvalidTransactionDataError(f"Data validation failed: {str(e)}")

def _is_transaction_table(df: pd.DataFrame) -> Tuple[bool, int]:
    """
    Check if the DataFrame represents a transaction table and identify header row.

    Args:
        df: DataFrame to check

    Returns:
        Tuple of (is_transaction_table, header_row_index)
        header_row_index will be 0 for first row, 1 for second row, or -1 if not a transaction table
    """
    def check_headers(row_values) -> bool:
        """Check if row contains required headers"""
        return any(
            all(col in row_values for col in pattern)
            for pattern in TRANSACTION_HEADERS
        )

    # Check first row
    if check_headers(df.iloc[0].values):
        return True, 0

    # Check second row
    if len(df) > 2 and check_headers(df.iloc[1].values):
        return True, 1

    return False, -1

def _process_table(df: pd.DataFrame, header_row: int) -> pd.DataFrame:
    """
    Process a transaction table with the identified header row.

    Args:
        df: DataFrame to process
        header_row: Index of the header row (0 or 1)

    Returns:
        Processed DataFrame with standardized columns
    """
    # Create a copy to avoid modifying the original
    df = df.copy()

    # Set headers and remove header rows
    df.columns = df.iloc[header_row]
    df = df.iloc[header_row + 1:].reset_index(drop=True)

    # Standardize column names
    df.columns = [str(col).strip().upper() for col in df.columns]

    # Clean up the DataFrame
    df = (df
          .dropna(how='all')  # Drop empty rows
          .dropna(axis=1, how='all')  # Drop empty columns
          # Keep only rows with valid transaction dates
          .loc[lambda x: x['TRANS\nDATE'].notna() & (x['TRANS\nDATE'] != '')]
          .reset_index(drop=True))

    return df

def format_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Format transaction data with standardized columns.

    Args:
        df: DataFrame with raw transaction data

    Returns:
        DataFrame with standardized columns:
        - transaction_date: from TRANS\nDATE
        - description: from TRANSACTION DETAILS (minus reference)
        - amount: positive for CREDIT, negative for DEBIT
        - reference_number: extracted from TRANSACTION DETAILS
    """
    # Initialize result DataFrame with transaction dates
    result = pd.DataFrame({
        'transaction_date': df['TRANS\nDATE'],
        'reference_number': df['TRANSACTION DETAILS'].str.extract(REFERENCE_PATTERN, expand=False)
    })

    # Process descriptions
    details = df['TRANSACTION DETAILS'].fillna('')
    result['description'] = (
        details.str.replace(REFERENCE_PATTERN, '', regex=True)
        .str.strip()
        .mask(lambda x: x == '', details)
    )

    # Clean and calculate amounts using vectorized operations
    def clean_amount(s):
        return (s.astype(str)
                .str.replace('Rs', '', regex=False)
                .str.replace(',', '', regex=False)
                .str.strip())

    debits = pd.to_numeric(
        clean_amount(df['DEBIT'].where(df['DEBIT'].notna() & (df['DEBIT'] != ''), '0')),
        errors='coerce'
    )
    credits = pd.to_numeric(
        clean_amount(df['CREDIT'].where(df['CREDIT'].notna() & (df['CREDIT'] != ''), '0')),
        errors='coerce'
    )
    result['amount'] = credits - debits

    # Validate the processed data
    validate_transaction_data(result)

    return result

def extract_transactions(file_path: Path) -> pd.DataFrame:
    """
    Process an MCB bank statement PDF file,
    identify transaction tables,
    exclude the non-transaction table,
    and aggregate the data from all the transaction tables found across the multiple pages of the PDF.

    Args:
        file_path: Path to the PDF file

    Returns:
        DataFrame containing the transaction data with proper column headers.

    Raises:
        StatementProcessingError: If there are issues processing the PDF
        NoTransactionTablesError: If no transaction tables are found
        InvalidTransactionDataError: If extracted data is invalid
    """
    logger.info(f"Processing statement: {file_path}")

    try:
        # Extract tables
        tables = camelot.read_pdf(
            str(file_path),
            pages='all',
            flavor='stream',
            edge_tol=100,
            row_tol=10
        )
    except Exception as e:
        raise StatementProcessingError(f"Failed to read PDF {file_path}: {str(e)}")

    logger.info(f"Found {len(tables)} tables")

    # Process each table and collect transaction tables
    transaction_dfs: List[pd.DataFrame] = []
    for idx, table in enumerate(tables, 1):
        try:
            is_trans, header_row = _is_transaction_table(table.df)
            if is_trans:
                logger.info(f"Found transaction table {idx} with header row {header_row}")
                processed_df = _process_table(table.df, header_row)
                transaction_dfs.append(processed_df)
            else:
                logger.debug(f"Table {idx} is not a transaction table")
        except Exception as e:
            logger.warning(f"Error processing table {idx}: {str(e)}")
            continue

    if not transaction_dfs:
        raise NoTransactionTablesError(f"No transaction tables found in {file_path}")

    try:
        # Combine all transaction tables
        result_df = pd.concat(transaction_dfs, ignore_index=True)
        result_df = result_df.loc[:, ~result_df.columns.str.match(r'^\s*$')]
        logger.info(f"Extracted {len(result_df)} transactions total")
        return result_df
    except Exception as e:
        raise StatementProcessingError(f"Failed to combine transaction tables: {str(e)}")
