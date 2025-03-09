"""
Database management module.
"""
from pathlib import Path
from .base import BaseDatabaseManager
from .transactions import TransactionManager
from .categories import CategoryManager
from .rules import RuleManager


class DatabaseManager(TransactionManager, CategoryManager, RuleManager):
    """
    Combined database manager that provides access to all operations.

    This class inherits from all specialized managers to provide a unified
    interface for database operations while keeping the implementation
    modular and maintainable.

    Usage:
        db = DatabaseManager(Path("data/finance.db"))
        db.initialize_database()

        # Transaction operations
        db.add_transactions(transactions)
        db.get_transactions(start_date="2024-01-01")

        # Category operations
        category_id = db.add_category("Groceries")
        categories = db.get_categories()

        # Rule operations
        rule_id = db.add_rule("WALMART", category_id)
        rules = db.get_rules()
    """

    def __init__(self, db_path: Path):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        super().__init__(db_path)


__all__ = ["DatabaseManager"]
