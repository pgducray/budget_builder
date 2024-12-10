"""
Script to process bank statements using the StatementLoader and DataCleaner.
"""
from pathlib import Path
from data_processing.loader import StatementLoader, DataCleaner
import pandas as pd

def main():
    # Initialize loader and cleaner
    loader = StatementLoader()
    cleaner = DataCleaner()

    # Get all files from data/raw
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(exist_ok=True)

    # Process each file
    for file_path in raw_dir.glob("*"):
        print(f"Processing {file_path.name}...")

        try:
            # Load the statement
            df = loader.load_statement(file_path)

            # Clean the data
            df = cleaner.standardize_columns(df)
            df = cleaner.clean_transaction_descriptions(df)
            df = loader.deduplicate_transactions(df)

            # Validate the data
            issues = cleaner.validate_data(df)
            if issues:
                print("Validation issues found:")
                for issue in issues:
                    print(f"  - {issue}")

            # Save to processed directory
            output_path = processed_dir / f"processed_{file_path.stem}.csv"
            df.to_csv(output_path, index=False)
            print(f"Saved processed file to {output_path}")

        except Exception as e:
            print(f"Error processing {file_path.name}: {str(e)}")

if __name__ == "__main__":
    main()
