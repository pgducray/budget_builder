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

    def add_transaction(
        self,
        date: str,
        description: str,
        amount: float,
        category_id: Optional[int] = None,
        rule_id: Optional[int] = None
    ) -> int:
        """
        Add a new transaction.

        Args:
            date: Transaction date (YYYY-MM-DD)
            description: Transaction description
            amount: Transaction amount
            reference_number: Optional reference number
            category_id: Optional category ID
            account_id: Optional account ID

        Returns:
            ID of the newly created transaction
        """
        logger = logging.getLogger(__name__)
        query = """
            INSERT INTO transactions (
                date,
                description,
                amount,
                category_id,
                rule_id
            ) VALUES (?, ?, ?, ?, ?)
            RETURNING id
        """

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    query,
                    (date, description, amount, category_id, rule_id)
                )
                transaction_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"Added transaction: {description} (ID: {transaction_id})")
                return transaction_id
        except sqlite3.Error as e:
            logger.error(f"Error adding transaction: {e}")
            raise

    def get_transactions(
        self,
        category_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve transactions with optional filters.

        Args:
            category_id: Filter by category ID
            start_date: Filter by start date (YYYY-MM-DD)
            end_date: Filter by end date (YYYY-MM-DD)
            min_amount: Filter by minimum amount
            max_amount: Filter by maximum amount
            limit: Maximum number of transactions to return

        Returns:
            List of transaction dictionaries
        """
        conditions = []
        params = []

        if category_id is not None:
            conditions.append("category_id = ?")
            params.append(category_id)
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        if min_amount is not None:
            conditions.append("amount >= ?")
            params.append(min_amount)
        if max_amount is not None:
            conditions.append("amount <= ?")
            params.append(max_amount)

        query = """
            SELECT
                id,
                date,
                description,
                amount,
                category_id,
                rule_id,
                created_at
            FROM transactions
        """

        if conditions:
            query += f" WHERE {' AND '.join(conditions)}"

        query += " ORDER BY date DESC"

        if limit:
            query += f" LIMIT {limit}"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_transaction(
        self,
        transaction_id: int,
        date: Optional[str] = None,
        description: Optional[str] = None,
        amount: Optional[float] = None,
        category_id: Optional[int] = None,
        rule_id: Optional[int] = None
    ) -> None:
        """
        Update a transaction.

        Args:
            transaction_id: ID of the transaction to update
            date: New date (optional)
            description: New description (optional)
            amount: New amount (optional)
            reference_number: New reference number (optional)
            category_id: New category ID (optional)
            account_id: New account ID (optional)
        """
        logger = logging.getLogger(__name__)
        updates = []
        params = []

        if date is not None:
            updates.append("date = ?")
            params.append(date)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if amount is not None:
            updates.append("amount = ?")
            params.append(amount)
        if category_id is not None:
            updates.append("category_id = ?")
            params.append(category_id)
        if rule_id is not None:
            updates.append("rule_id = ?")
            params.append(rule_id)

        if not updates:
            return

        query = f"""
            UPDATE transactions
            SET {", ".join(updates)}
            WHERE id = ?
        """
        params.append(transaction_id)

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, params)
                conn.commit()
                logger.info(f"Updated transaction {transaction_id}")
        except sqlite3.Error as e:
            logger.error(f"Error updating transaction: {e}")
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

    def get_uncategorized_transactions(self) -> List[Dict[str, Any]]:
        """
        Get all uncategorized transactions.

        Returns:
            List of uncategorized transaction dictionaries
        """
        return self.get_transactions(category_id=None)

    def update_transaction_category(
        self,
        transaction_id: int,
        category_id: Optional[int]
    ) -> None:
        """
        Update a transaction's category.

        Args:
            transaction_id: ID of the transaction to update
            category_id: New category ID (None for uncategorized)
        """
        self.update_transaction(transaction_id, category_id=category_id)
