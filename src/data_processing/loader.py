"""
Module for loading bank statement data.
Specifically designed for MCB bank statements in PDF format.
"""
from typing import Optional
import pandas as pd
from pathlib import Path
import camelot
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StatementLoader:
    """Handles loading and initial preprocessing of MCB bank statements."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize with data directory path."""
        self.data_dir = Path("data/raw") if data_dir is None else data_dir

    def load_statement(self, file_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Load an MCB bank statement PDF file.

        Args:
            file_path: Path to the PDF file. If None, uses the first PDF in data_dir.

        Returns:
            DataFrame containing the transaction data with proper column headers.
        """
        # Handle default file path
        if file_path is None:
            pdf_files = list(self.data_dir.glob('*.pdf'))
            if not pdf_files:
                raise FileNotFoundError(f"No PDF files found in {self.data_dir}")
            file_path = pdf_files[0]

        logger.info(f"Processing statement: {file_path}")

        # Extract tables using stream mode with optimized parameters
        tables = camelot.read_pdf(
            str(file_path),
            pages='all',
            flavor='stream',
            edge_tol=100,  # Optimized for MCB statements
            row_tol=10     # Optimized for MCB statements
        )

        logger.info(f"Found {len(tables)} tables")

        if len(tables) < 2:
            raise ValueError("Expected at least 2 tables in the PDF")

        # Get the data table (second table)
        data_table = tables[1].df

        # Remove the text from header table (first row)
        data_table = data_table.iloc[1:].reset_index(drop=True)

        # Set the first row as column headers
        headers = data_table.iloc[0]
        data_table = data_table.iloc[1:].reset_index(drop=True)
        data_table.columns = headers

        # Convert dates to datetime
        date_columns = data_table.columns[data_table.columns.str.contains('Date', case=False)]
        for col in date_columns:
            data_table[col] = pd.to_datetime(data_table[col], format='%d/%m/%Y', errors='coerce')

        # Convert numeric columns (amounts)
        amount_columns = data_table.columns[
            data_table.columns.str.contains('Amount|Balance|Credit|Debit', case=False)
        ]
        for col in amount_columns:
            data_table[col] = pd.to_numeric(
                data_table[col].str.replace(',', ''),
                errors='coerce'
            )

        # Extract transaction reference numbers from TRANSACTION DETAILS
        data_table['transaction reference number'] = data_table['TRANSACTION DETAILS'].str.extract(r'(FT\w+\\BNK)')

        # Remove the reference numbers from TRANSACTION DETAILS
        data_table['TRANSACTION DETAILS'] = data_table['TRANSACTION DETAILS'].str.replace(r'FT\w+\\BNK\s*', '', regex=True)

        logger.info(f"Extracted {len(data_table)} transactions")
        return data_table
