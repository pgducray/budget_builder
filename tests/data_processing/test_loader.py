"""
Tests for the statement loader module.
"""
import pytest
from pathlib import Path
from src.data_processing.loader import StatementLoader


@pytest.fixture
def loader():
    return StatementLoader()


def test_detect_file_type(loader):
    """Test file type detection"""
    assert loader.detect_file_type(Path("test.pdf")) == "pdf"
    assert loader.detect_file_type(Path("test.csv")) == "csv"
    with pytest.raises(ValueError):
        loader.detect_file_type(Path("test.txt"))


def test_is_date(loader):
    """Test date validation"""
    assert loader._is_date("01/03/2024")
    assert loader._is_date("31/12/2023")
    assert not loader._is_date("2024/03/01")
    assert not loader._is_date("01-03-2024")
    assert not loader._is_date("Some text")
    assert not loader._is_date("")
    assert not loader._is_date(None)


def test_is_amount(loader):
    """Test amount validation"""
    assert loader._is_amount("500.00")
    assert loader._is_amount("-500.00")
    assert loader._is_amount("1,234.56")
    assert loader._is_amount("-1,234.56")
    assert not loader._is_amount("500")
    assert not loader._is_amount("500.0")
    assert not loader._is_amount("Some text")
    assert not loader._is_amount("")
    assert not loader._is_amount(None)


def test_clean_amount(loader):
    """Test amount cleaning"""
    assert loader._clean_amount("500.00") == 500.00
    assert loader._clean_amount("-500.00") == -500.00
    assert loader._clean_amount("1,234.56") == 1234.56
    assert loader._clean_amount("-1,234.56") == -1234.56
    assert loader._clean_amount("Some text 500.00") == 500.00
    assert loader._clean_amount("") is None
    assert loader._clean_amount(None) is None


def test_is_transaction_row(loader):
    """Test transaction row validation"""
    # Valid transaction row
    assert loader._is_transaction_row([
        "01/03/2024",
        "02/03/2024",
        "PAYMENT TO JOHN",
        "500.00",
        "1,234.56"
    ])

    # Invalid rows
    assert not loader._is_transaction_row([])  # Empty row
    assert not loader._is_transaction_row(["01/03/2024"])  # Too short
    assert not loader._is_transaction_row([
        "Not a date",
        "02/03/2024",
        "PAYMENT",
        "500.00"
    ])  # First column not a date
    assert not loader._is_transaction_row([
        "01/03/2024",
        "Not a date",
        "PAYMENT",
        "500.00"
    ])  # Second column not a date
    assert not loader._is_transaction_row([
        "01/03/2024",
        "02/03/2024",
        "PAYMENT",
        "Not an amount"
    ])  # No valid amounts


def test_process_table(loader):
    """Test table processing"""
    table = [
        ["Date", "Value Date", "Description", "Amount", "Balance"],  # Header row
        ["01/03/2024", "02/03/2024", "PAYMENT TO JOHN", "500.00", "1,234.56"],
        ["03/03/2024", "04/03/2024", "SALARY", "-2000.00", "3,234.56"],
        ["Invalid", "Row", "Should", "Be", "Skipped"],
    ]

    transactions = loader._process_table(table)

    assert len(transactions) == 2  # Should only process valid transaction rows

    # Verify first transaction
    assert transactions[0]["trans_date"] == "01/03/2024"
    assert transactions[0]["value_date"] == "02/03/2024"
    assert transactions[0]["transaction_details"] == "PAYMENT TO JOHN"
    assert transactions[0]["debit"] == "500.00"
    assert transactions[0]["credit"] is None
    assert transactions[0]["balance"] == "1234.56"

    # Verify second transaction
    assert transactions[1]["trans_date"] == "03/03/2024"
    assert transactions[1]["value_date"] == "04/03/2024"
    assert transactions[1]["transaction_details"] == "SALARY"
    assert transactions[1]["debit"] is None
    assert transactions[1]["credit"] == "2000.00"
    assert transactions[1]["balance"] == "3234.56"


def test_empty_table_processing(loader):
    """Test processing of empty or invalid tables"""
    # Empty table
    assert loader._process_table([]) == []

    # Table with only headers
    assert loader._process_table([
        ["Date", "Value Date", "Description", "Amount", "Balance"]
    ]) == []

    # Table with invalid rows
    assert loader._process_table([
        ["Invalid", "Data", "Row"],
        ["Still", "Invalid", "Row"]
    ]) == []
