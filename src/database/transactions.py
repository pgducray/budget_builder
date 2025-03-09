"""
Transaction-related database operations.
"""
import logging
from typing import List, Dict, Any, Optional
import sqlite3
from datetime import datetime
from .base import BaseDatabaseManager


class TransactionManager(BaseDatabaseManager):
    """Handles transaction-related database operations."""

    def add_transactions(self, transactions: List[Dict[str, Any]]) -> None:
        """
        Add multiple transactions to the database.

        Args:
            transactions: List of transaction dictionaries with keys:
                - transaction_date
                - description
                - amount
                - reference_number (optional)
                - category_id (optional)
                - account_id (optional)
        """
        logger = logging.getLogger(__name__)
        insert_query = """
            INSERT OR IGNORE INTO transactions (
                transaction_date,
                description,
                amount,
                reference_number,
                category_id,
                account_id
            ) VALUES (?, ?, ?, ?, ?, ?)
        """

        try:
            with sqlite3.connect(self.db_path) as conn:
                for transaction in transactions:
                    transaction_date_str = transaction['transaction_date'].strftime('%Y-%m-%d') if isinstance(transaction['transaction_date'], datetime) else transaction['transaction_date']
                    conn.execute(
                        insert_query,
                        (
                            transaction_date_str,
                            transaction['description'],
                            transaction['amount'],
                            transaction.get('reference_number'),
                            transaction.get('category_id'),
                            transaction.get('account_id')
                        )
                    )
                conn.commit()
                logger.info(f"Added {len(transactions)} transactions to database")
        except sqlite3.Error as e:
            logger.error(f"Error adding transactions: {e}")
            raise

    def get_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve transactions based on filters.

        Args:
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            category_id: Optional category filter

        Returns:
            List of transaction dictionaries
        """
        query = """
            SELECT
                id,
                transaction_date,
                description,
                amount,
                category_id,
                account_id,
                created_at
            FROM transactions
            WHERE 1=1
        """
        params = []

        if start_date:
            query += " AND transaction_date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND transaction_date <= ?"
            params.append(end_date)

        if category_id is not None:
            query += " AND category_id = ?"
            params.append(category_id)

        query += " ORDER BY transaction_date DESC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_transaction_category(
        self,
        transaction_id: int,
        category_id: Optional[int]
    ) -> None:
        """
        Update the category of a transaction.

        Args:
            transaction_id: ID of the transaction to update
            category_id: New category ID (None to remove categorization)
        """
        logger = logging.getLogger(__name__)
        query = "UPDATE transactions SET category_id = ? WHERE id = ?"

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, (category_id, transaction_id))
                conn.commit()
                logger.info(f"Updated category for transaction {transaction_id}")
        except sqlite3.Error as e:
            logger.error(f"Error updating transaction category: {e}")
            raise

    def delete_transaction(self, transaction_id: int) -> None:
        """
        Delete a transaction.

        Args:
            transaction_id: ID of the transaction to delete
        """
        logger = logging.getLogger(__name__)
        query = "DELETE FROM transactions WHERE id = ?"

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, (transaction_id,))
                conn.commit()
                logger.info(f"Deleted transaction {transaction_id}")
        except sqlite3.Error as e:
            logger.error(f"Error deleting transaction: {e}")
            raise
