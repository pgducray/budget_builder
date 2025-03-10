"""
Rule-related database operations.
"""
import logging
from typing import List, Dict, Any
import sqlite3
from .base import BaseDatabaseManager


class RuleManager(BaseDatabaseManager):
    """Handles rule-related database operations."""

    def add_rule(
        self,
        pattern: str,
        category_id: int,
        priority: int = 0,
        is_regex: bool = False
    ) -> int:
        """
        Add a new categorization rule.

        Args:
            pattern: Rule pattern to match
            category_id: Category ID to assign
            priority: Rule priority (higher numbers = higher priority)
            is_regex: Whether pattern is a regular expression

        Returns:
            ID of the newly created rule
        """
        logger = logging.getLogger(__name__)
        query = """
            INSERT INTO categorization_rules (
                pattern,
                category_id,
                priority,
                is_regex
            ) VALUES (?, ?, ?, ?)
            RETURNING id
        """

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    query,
                    (pattern, category_id, priority, is_regex)
                )
                rule_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"Added rule: {pattern} (ID: {rule_id})")
                return rule_id
        except sqlite3.Error as e:
            logger.error(f"Error adding rule: {e}")
            raise

    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Retrieve all categorization rules.

        Returns:
            List of rule dictionaries
        """
        query = """
            SELECT
                id,
                pattern,
                category_id,
                priority,
                is_regex,
                created_at
            FROM categorization_rules
            ORDER BY priority DESC, created_at DESC
        """

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def update_rule(
        self,
        rule_id: int,
        pattern: str = None,
        category_id: int = None,
        priority: int = None,
        is_regex: bool = None
    ) -> None:
        """
        Update a categorization rule.

        Args:
            rule_id: ID of the rule to update
            pattern: New pattern (optional)
            category_id: New category ID (optional)
            priority: New priority (optional)
            is_regex: New regex flag (optional)
        """
        logger = logging.getLogger(__name__)
        updates = []
        params = []

        if pattern is not None:
            updates.append("pattern = ?")
            params.append(pattern)
        if category_id is not None:
            updates.append("category_id = ?")
            params.append(category_id)
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        if is_regex is not None:
            updates.append("is_regex = ?")
            params.append(is_regex)

        if not updates:
            return

        query = f"""
            UPDATE categorization_rules
            SET {", ".join(updates)}
            WHERE id = ?
        """
        params.append(rule_id)

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, params)
                conn.commit()
                logger.info(f"Updated rule {rule_id}")
        except sqlite3.Error as e:
            logger.error(f"Error updating rule: {e}")
            raise

    def delete_rule(self, rule_id: int) -> None:
        """
        Delete a categorization rule.

        Args:
            rule_id: ID of the rule to delete
        """
        logger = logging.getLogger(__name__)
        query = "DELETE FROM categorization_rules WHERE id = ?"

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, (rule_id,))
                conn.commit()
                logger.info(f"Deleted rule {rule_id}")
        except sqlite3.Error as e:
            logger.error(f"Error deleting rule: {e}")
            raise

    def import_rules(
        self,
        rules: List[Dict[str, Any]],
        clear_existing: bool = False
    ) -> None:
        """
        Import rules from a list.

        Args:
            rules: List of rule dictionaries
            clear_existing: Whether to clear existing rules first
        """
        logger = logging.getLogger(__name__)

        try:
            with sqlite3.connect(self.db_path) as conn:
                if clear_existing:
                    conn.execute("DELETE FROM categorization_rules")

                for rule in rules:
                    conn.execute(
                        """
                        INSERT INTO categorization_rules (
                            pattern,
                            category_id,
                            priority,
                            is_regex
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (
                            rule["pattern"],
                            rule["category_id"],
                            rule.get("priority", 0),
                            rule.get("is_regex", False)
                        )
                    )
                conn.commit()
                logger.info(f"Imported {len(rules)} rules")
        except sqlite3.Error as e:
            logger.error(f"Error importing rules: {e}")
            raise
