"""
Tests for the statement loader module.
"""
import pytest
import pandas as pd
from pathlib import Path
from src.data_processing.loader import StatementLoader, DataCleaner


@pytest.fixture
def loader():
    return StatementLoader()

@pytest.fixture
def cleaner():
    return DataCleaner()

def test_detect_file_type(loader):
    """Test file type detection"""
    assert loader.detect_file_type(Path("test.pdf")) == "pdf"
    assert loader.detect_file_type(Path("test.csv")) == "csv"
    with pytest.raises(ValueError):
        loader.detect_file_type(Path("test.txt"))

def test_deduplicate_transactions(loader):
    """Test deduplication of transactions"""
    df = pd.DataFrame({
        'date': ['2023-01-01', '2023-01-01'],
        'description': ['Test', 'Test'],
        'amount': [100, 100]
    })
    result = loader.deduplicate_transactions(df)
    assert len(result) == 1

def test_standardize_columns(cleaner):
    """Test column standardization"""
    df = pd.DataFrame({
        'Date': ['2023-01-01'],
        'Transaction Description': ['Test'],
        'Amount': [100]
    })
    result = cleaner.standardize_columns(df)
    assert 'date' in result.columns
    assert 'description' in result.columns
    assert 'amount' in result.columns

def test_clean_transaction_descriptions(cleaner):
    """Test transaction description cleaning"""
    df = pd.DataFrame({
        'description': ['  Test Description  ', 'Another Test  ']
    })
    result = cleaner.clean_transaction_descriptions(df)
    assert result['description'].iloc[0] == 'TEST DESCRIPTION'
    assert result['description'].iloc[1] == 'ANOTHER TEST'

def test_validate_data(cleaner):
    """Test data validation"""
    df = pd.DataFrame({
        'date': ['2023-01-01', None],
        'description': ['Test', 'Test'],
        'amount': [100, None]
    })
    issues = cleaner.validate_data(df)
    assert len(issues) > 0
    assert any(issue['type'] == 'missing_values' for issue in issues)
