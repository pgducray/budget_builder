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

        queries = [
            # Transactions table
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_date DATE NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                reference_number TEXT,
                category_id INTEGER,
                account_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id),
                FOREIGN KEY (account_id) REFERENCES accounts (id)
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_ref
            ON transactions(reference_number)
            WHERE reference_number IS NOT NULL;

            CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_date_desc
            ON transactions(transaction_date, description)
            WHERE reference_number IS NULL
            """,

            # Categories table
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                parent_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES categories (id)
            )
            """,

            # Accounts table
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
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
            """
        ]

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                for query in queries:
                    conn.executescript(query)
                conn.commit()
                logger.info("Database schema initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
