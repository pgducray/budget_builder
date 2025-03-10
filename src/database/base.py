"""
Base database manager functionality.
"""
import logging
import sqlite3
from pathlib import Path


class BaseDatabaseManager:
    """Base class for database operations."""

    def __init__(self, db_path: Path):
        """
        Initialize database connection and setup.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

    def initialize_database(self) -> None:
        """Create database schema if it doesn't exist."""
        logger = logging.getLogger(__name__)
        logger.info(f"Initializing database at {self.db_path}")

        # Create tables and indexes
        queries = [
            # Categories table with self-reference
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                parent_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES categories (id)
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_categories_parent
            ON categories(parent_id)
            """,

            # Categorization rules table
            """
            CREATE TABLE IF NOT EXISTS categorization_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                priority INTEGER DEFAULT 0,
                is_regex BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_rules_category
            ON categorization_rules(category_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_rules_pattern
            ON categorization_rules(pattern)
            """,

            # Transactions table
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category_id INTEGER,
                rule_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id),
                FOREIGN KEY (rule_id) REFERENCES categorization_rules (id)
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_transactions_date
            ON transactions(date)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_transactions_category
            ON transactions(category_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_transactions_rule
            ON transactions(rule_id)
            """
        ]

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                for query in queries:
                    conn.execute(query)
                conn.commit()
                logger.info("Database schema initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
