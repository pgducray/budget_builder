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
        'trace': {  # Changed from 'figure' to 'trace'
            'height': 400,
            'width': None  # Use container width
        },
        'layout': {
            'height': 400,
            'showlegend': True,
            'margin': {'l': 150},  # Add left margin for category labels
            'xaxis': {
                'title': "Amount (Rs)",
                'showgrid': True,
                'tickangle': -45
            },
            'yaxis': {
                'title': "Category",
                'showgrid': True
            }
        }
    },
    'line': {
        'layout': {
            'height': 400,
            'showlegend': True,
            'xaxis': {
                'title': None,
                'showgrid': True
            },
            'yaxis': {
                'showgrid': True
            },
            'hovermode': 'x unified'
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
