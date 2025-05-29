"""
Script to categorize transactions from the unified transaction database.
"""
import pandas as pd
from pathlib import Path
from categorization.simple_categorizer import SimpleTransactionCategorizer

def main():
    """Categorize transactions from the unified database."""
    try:
        # Load unified transactions
        transactions_path = Path("data/transactions.csv")
        if not transactions_path.exists():
            print("Error: No unified transaction database found.")
            print("Please run process_statements.py first to create the unified database.")
            return

        df = pd.read_csv(transactions_path)
        print(f"\nLoaded {len(df)} transactions")

        # Initialize categorizer
        categorizer = SimpleTransactionCategorizer()

        # Categorize transactions
        categorized_df = categorizer.categorize_transactions(df)

        # Get and display summary
        summary = categorizer.get_category_summary(categorized_df)
        print("\nCategory Summary:")
        print(summary)

        # Save categorized transactions
        output_path = Path("data/categorized_transactions.csv")
        categorized_df.to_csv(output_path, index=False)
        print(f"\nSaved categorized transactions to: {output_path}")

    except Exception as e:
        print(f"Error processing transactions: {str(e)}")

if __name__ == "__main__":
    main()
