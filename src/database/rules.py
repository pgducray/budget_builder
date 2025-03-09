"""
Categorization rule database operations.
"""
import logging
from typing import List, Dict, Any, Optional
import sqlite3
from .base import BaseDatabaseManager


class RuleManager(BaseDatabaseManager):
    """Handles categorization rule database operations."""

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
            pattern: Text pattern to match
            category_id: ID of the category to assign
            priority: Rule priority (higher numbers take precedence)
            is_regex: Whether the pattern is a regular expression

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
                logger.info(f"Added categorization rule: {pattern} (ID: {rule_id})")
                return rule_id
        except sqlite3.Error as e:
            logger.error(f"Error adding categorization rule: {e}")
            raise

    def get_rules(
        self,
        category_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve categorization rules.

        Args:
            category_id: Optional category filter

        Returns:
            List of rule dictionaries
        """
        query = """
            SELECT
                r.id,
                r.pattern,
                r.category_id,
                c.name as category_name,
                r.priority,
                r.is_regex,
                r.created_at
            FROM categorization_rules r
            JOIN categories c ON r.category_id = c.id
        """
        params = []

        if category_id is not None:
            query += " WHERE r.category_id = ?"
            params.append(category_id)

        query += " ORDER BY r.priority DESC, r.created_at ASC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_rule(
        self,
        rule_id: int,
        pattern: Optional[str] = None,
        category_id: Optional[int] = None,
        priority: Optional[int] = None,
        is_regex: Optional[bool] = None
    ) -> None:
        """
        Update an existing rule.

        Args:
            rule_id: ID of the rule to update
            pattern: New pattern (optional)
            category_id: New category ID (optional)
            priority: New priority (optional)
            is_regex: New is_regex value (optional)
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
                logger.info(f"Updated categorization rule {rule_id}")
        except sqlite3.Error as e:
            logger.error(f"Error updating categorization rule: {e}")
            raise

    def delete_rule(self, rule_id: int) -> None:
        """
        Delete a rule.

        Args:
            rule_id: ID of the rule to delete
        """
        logger = logging.getLogger(__name__)
        query = "DELETE FROM categorization_rules WHERE id = ?"

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, (rule_id,))
                conn.commit()
                logger.info(f"Deleted categorization rule {rule_id}")
        except sqlite3.Error as e:
            logger.error(f"Error deleting categorization rule: {e}")
            raise

    def import_rules(
        self,
        rules: List[Dict[str, Any]],
        clear_existing: bool = False
    ) -> None:
        """
        Import multiple rules.

        Args:
            rules: List of rule dictionaries
            clear_existing: Whether to delete existing rules first
        """
        logger = logging.getLogger(__name__)

        try:
            with sqlite3.connect(self.db_path) as conn:
                if clear_existing:
                    conn.execute("DELETE FROM categorization_rules")

                query = """
                    INSERT INTO categorization_rules (
                        pattern,
                        category_id,
                        priority,
                        is_regex
                    ) VALUES (?, ?, ?, ?)
                """

                for rule in rules:
                    conn.execute(
                        query,
                        (
                            rule["pattern"],
                            rule["category_id"],
                            rule.get("priority", 0),
                            rule.get("is_regex", False)
                        )
                    )

                conn.commit()
                logger.info(f"Imported {len(rules)} categorization rules")
        except sqlite3.Error as e:
            logger.error(f"Error importing categorization rules: {e}")
            raise
