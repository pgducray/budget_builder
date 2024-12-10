"""
Module for loading and preprocessing bank statement data.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
from pathlib import Path
import PyPDF2
import re


class StatementLoader:
    """Handles loading and initial preprocessing of bank statements."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize with data directory path."""
        self.data_dir = Path("data/raw") if data_dir is None else data_dir

    def detect_file_type(self, file_path: Path) -> str:
        """Detect file type (PDF or CSV)."""
        suffix = file_path.suffix.lower()
        if suffix not in ['.pdf', '.csv']:
            raise ValueError(f"Unsupported file type: {suffix}")
        return suffix[1:]  # Remove the dot

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract amount from text, handling commas in numbers."""
        match = re.search(r'-?[\d,]+\.\d{2}', text)
        if match:
            return float(match.group().replace(',', ''))
        return None

    def _is_table_header(self, line: str) -> bool:
        """Check if line is a table header."""
        header_terms = [
            'TRANS DATE', 'VALUE DATE', 'TRANSACTION DETAILS',
            'DEBIT', 'CREDIT', 'BALANCE'
        ]
        return any(term in line for term in header_terms)

    def _is_page_header_or_footer(self, line: str) -> bool:
        """Check if line is part of page header or footer."""
        patterns = [
            r'Savings Regular Account STATEMENT Page',
            r'01RB0801 MA',
            r'The Mauritius Commercial Bank Ltd',
            r'Swift Code:',
            r'Website:',
            r'IBAN:',
            r'Account Number',
            r'Currency',
            r'Statement Date',
            r'Despatch Code'
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns)

    def _process_transaction_line(self, line: str, previous_balance: float) -> Optional[Dict[str, Any]]:
        """Process a single transaction line."""
        # Extract dates (DD/MM/YYYY format)
        dates = re.findall(r'\d{2}/\d{2}/\d{4}', line)

        # If there are no dates but there is text, this might be a continuation line
        if len(dates) < 2:
            # Clean the line and check if it contains any meaningful text
            cleaned_line = ' '.join(line.split())  # Normalize whitespace
            if cleaned_line:  # If there's any text, return None with the text
                return {'continuation_text': cleaned_line}
            return None

        # Remove dates from text
        details = re.sub(r'\d{2}/\d{2}/\d{4}', '', line)

        # Extract amounts
        amounts = re.findall(r'-?[\d,]+\.\d{2}', details)
        if not amounts:
            return None

        # Second amount is always the balance
        balance = float(amounts[1].replace(',', ''))

        # Check if transaction is debit or credit
        credit = debit = None
        if balance > previous_balance:
            credit = amounts[0]
        else:
            debit = amounts[0]

        # Clean transaction details
        details = re.sub(r'-?[\d,]+\.\d{2}', '', details)
        details = ' '.join(details.split())  # Normalize whitespace

        return {
            'trans_date': dates[0],
            'value_date': dates[1],
            'transaction_details': details.strip(),
            'debit': debit,
            'credit': credit,
            'balance': balance
        }

    def extract_table_from_pdf_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract transaction data from PDF text."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        transactions = []

        # Find opening balance
        for idx, line in enumerate(lines):
            if 'OPENING BALANCE' in line.upper():
                opening_balance = self._extract_amount(line)
                if opening_balance is not None:
                    transactions.append({
                        'trans_date': None,
                        'value_date': None,
                        'transaction_details': 'OPENING BALANCE',
                        'debit': None,
                        'credit': None,
                        'balance': opening_balance
                    })
                break

        # Process transaction lines
        balance = 0.0
        for line in lines:
            # Skip headers/footers and empty lines
            if not line or self._is_table_header(line) or self._is_page_header_or_footer(line):
                continue

            # Process transaction
            result = self._process_transaction_line(line, balance)
            if result:
                if 'continuation_text' in result:
                    # If this is a continuation line and we have previous transactions,
                    # append the text to the last transaction's details
                    if transactions:
                        transactions[-1]['transaction_details'] += ' ' + result['continuation_text']
                else:
                    # Regular transaction line
                    balance = result['balance']
                    transactions.append(result)

        return transactions

    def load_pdf_statement(self, file_path: Path) -> pd.DataFrame:
        """Load and process a PDF bank statement."""
        with open(file_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            text = ' '.join(page.extract_text() for page in pdf.pages)

        transactions = self.extract_table_from_pdf_text(text)

        if not transactions:
            return pd.DataFrame(columns=[
                'trans_date', 'value_date', 'transaction_details',
                'debit', 'credit', 'balance'
            ])

        df = pd.DataFrame(transactions)

        # Convert dates to datetime
        for date_col in ['trans_date', 'value_date']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], format='%d/%m/%Y', errors='coerce')

        return df

    def load_csv_statement(self, file_path: Path) -> pd.DataFrame:
        """Load a CSV bank statement."""
        return pd.read_csv(file_path)

    def load_statement(self, file_path: Optional[Path] = None) -> pd.DataFrame:
        """Load a bank statement file."""
        if file_path is None:
            files = list(self.data_dir.glob('*'))
            if not files:
                raise FileNotFoundError(f"No files found in {self.data_dir}")
            file_path = files[0]

        file_type = self.detect_file_type(file_path)
        loader = self.load_pdf_statement if file_type == 'pdf' else self.load_csv_statement
        return loader(file_path)

    def deduplicate_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate transactions."""
        return df.drop_duplicates()


class DataCleaner:
    """Handles cleaning and standardization of transaction data."""

    def standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names and ensure required columns exist."""
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]

        required_columns = [
            'trans_date', 'value_date', 'transaction_details',
            'debit', 'credit', 'balance'
        ]
        for col in required_columns:
            if col not in df.columns:
                df[col] = None

        return df

    def clean_transaction_descriptions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize transaction descriptions."""
        if 'transaction_details' in df.columns:
            df['transaction_details'] = (df['transaction_details']
                .str.strip()
                .str.upper()
                .fillna(''))

        return df

    def validate_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Validate data quality and completeness."""
        issues = []

        # Check missing values (excluding opening balance)
        df_transactions = df[df['transaction_details'] != 'OPENING BALANCE']
        missing_values = df_transactions.isnull().sum()

        for column, count in missing_values.items():
            if count > 0 and column not in ['debit', 'credit']:
                issues.append({
                    'type': 'missing_values',
                    'column': column,
                    'count': count
                })

        # Check for invalid transactions (both debit and credit)
        invalid_count = len(df_transactions[
            df_transactions['debit'].notna() &
            df_transactions['credit'].notna()
        ])
        if invalid_count > 0:
            issues.append({
                'type': 'invalid_transaction',
                'message': f'Found {invalid_count} transactions with both debit and credit'
            })

        return issues
