"""
Interactive script for refining transaction categorization patterns.
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict
from categorization.simple_categorizer import SimpleTransactionCategorizer

def display_category_stats(df: pd.DataFrame) -> None:
    """Display statistics about categorization results."""
    total = len(df)
    uncategorized = len(df[df['Category'] == 'Uncategorized'])
    print("\nCategorization Statistics:")
    print(f"Total Transactions: {total}")
    print(f"Categorized: {total - uncategorized} ({((total - uncategorized)/total)*100:.1f}%)")
    print(f"Uncategorized: {uncategorized} ({(uncategorized/total)*100:.1f}%)")

def display_transactions(df: pd.DataFrame, category: str, limit: int = 5) -> None:
    """Display sample transactions for a category."""
    transactions = df[df['Category'] == category]
    if len(transactions) == 0:
        return

    print(f"\n{category} Transactions (showing {min(limit, len(transactions))} of {len(transactions)}):")
    for _, row in transactions.head(limit).iterrows():
        pattern = row['Matching Pattern'] or 'No matching pattern'
        print(f"Description: {row['description']}")
        print(f"Amount: {row['amount']}")
        print(f"Matching Pattern: {pattern}")
        print("-" * 80)

def get_user_input(prompt: str, options: List[str] = None) -> str:
    """Get user input with optional validation against a list of options."""
    while True:
        value = input(prompt).strip()
        if not options or value in options:
            return value
        print(f"Please enter one of: {', '.join(options)}")

def main():
    """Run the pattern refinement workflow."""
    try:
        # Load transactions
        transactions_path = Path("data/transactions.csv")
        patterns_path = Path("data/patterns.json")

        if not transactions_path.exists():
            print("Error: No transaction database found.")
            print("Please run process_statements.py first to create the unified database.")
            return

        df = pd.read_csv(transactions_path)
        print(f"\nLoaded {len(df)} transactions")

        # Initialize categorizer with existing patterns if available
        categorizer = SimpleTransactionCategorizer(
            SimpleTransactionCategorizer.load_patterns(patterns_path)
        )

        while True:
            # Categorize transactions with current patterns
            categorized_df = categorizer.categorize_transactions(df)

            # Display statistics
            display_category_stats(categorized_df)

            # Show summary by category
            summary = categorizer.get_category_summary(categorized_df)
            print("\nCategory Summary:")
            print(summary)

            # Menu options
            print("\nOptions:")
            print("1. View uncategorized transactions")
            print("2. View transactions by category")
            print("3. Add new pattern")
            print("4. Remove pattern")
            print("5. Save patterns and exit")
            print("6. Exit without saving")

            choice = get_user_input("\nEnter choice (1-6): ", ['1', '2', '3', '4', '5', '6'])

            if choice == '1':
                display_transactions(categorized_df, 'Uncategorized')

            elif choice == '2':
                categories = categorized_df['Category'].unique()
                print("\nAvailable categories:")
                for i, cat in enumerate(categories, 1):
                    print(f"{i}. {cat}")
                cat_num = get_user_input("\nEnter category number: ", [str(i) for i in range(1, len(categories) + 1)])
                display_transactions(categorized_df, categories[int(cat_num) - 1])

            elif choice == '3':
                pattern = get_user_input("\nEnter regex pattern: ")
                category = get_user_input("Enter category name: ")
                categorizer.add_pattern(pattern, category)
                print("Pattern added successfully")

            elif choice == '4':
                print("\nCurrent patterns:")
                for pattern, category in categorizer.patterns.items():
                    print(f"Pattern: {pattern}")
                    print(f"Category: {category}")
                    print("-" * 40)
                pattern = get_user_input("\nEnter pattern to remove: ")
                categorizer.remove_pattern(pattern)
                print("Pattern removed successfully")

            elif choice == '5':
                categorizer.save_patterns(patterns_path)
                print(f"\nPatterns saved to: {patterns_path}")
                break

            elif choice == '6':
                print("\nExiting without saving changes")
                break

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
