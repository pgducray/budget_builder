"""
Configuration settings for the Transaction Categorizer.
"""

# Default categories for transaction classification
CATEGORIES = [
    "Income",
    "Groceries",
    "Restaurants",
    "Coffee Shops",
    "Shopping",
    "Transportation & Fuel",
    "Sport",
    "Utilities",
    "Entertainment",
    "Healthcare",
    "Insurance",
    "Bank Charges",
    "Taxes",
    "Travel",
    "Education",
    "Home",
    "Subscriptions",
    "Internal Transfert",
    "Other"
]

# Chart configurations
CHART_CONFIG = {
    'pie': {
        'figure': {
            'title': "Transaction Distribution by Category",
            'height': 400,
            'width': None  # Use container width
        },
        'layout': {
            'showlegend': True
        }
    },
    'bar': {
        'figure': {
            'title': "Transaction Frequency and Amounts",
            'height': 400,
            'width': None,  # Use container width
            'barmode': 'group',
            'xaxis': {
                'title': "Transaction Description",
                'tickangle': -45
            },
            'yaxis': {
                'title': "Count / Amount"
            }
        }
    }
}

# Display configurations
DISPLAY_CONFIG = {
    'transactions_columns': ['description', 'amount', 'Category', 'Matching Pattern'],
    'preview_columns': ['description', 'amount', 'Category'],
    'pattern_list_columns': ['Pattern', 'Category', 'Matching Transactions'],
    'pattern_list_widths': [3, 2, 2, 1],  # Column widths for pattern list
    'frequency_limit': 25  # Number of transactions to show in frequency analysis
}
