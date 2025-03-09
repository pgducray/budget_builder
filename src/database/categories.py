"""
Category-related database operations.
"""
import logging
from typing import List, Dict, Any, Optional
import sqlite3
from .base import BaseDatabaseManager


class CategoryManager(BaseDatabaseManager):
    """Handles category-related database operations."""

    def add_category(
        self,
        name: str,
        parent_id: Optional[int] = None
    ) -> int:
        """
        Add a new category.

        Args:
            name: Category name
            parent_id: Optional parent category ID

        Returns:
            ID of the newly created category
        """
        logger = logging.getLogger(__name__)
        query = """
            INSERT INTO categories (name, parent_id)
            VALUES (?, ?)
            RETURNING id
        """

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, (name, parent_id))
                category_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"Added category: {name} (ID: {category_id})")
                return category_id
        except sqlite3.Error as e:
            logger.error(f"Error adding category: {e}")
            raise

    def get_categories(
        self,
        parent_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve categories.

        Args:
            parent_id: Optional parent category ID filter

        Returns:
            List of category dictionaries
        """
        query = """
            SELECT
                c1.id,
                c1.name,
                c1.parent_id,
                c2.name as parent_name,
                c1.created_at
            FROM categories c1
            LEFT JOIN categories c2 ON c1.parent_id = c2.id
        """
        params = []

        if parent_id is not None:
            query += " WHERE c1.parent_id = ?"
            params.append(parent_id)

        query += " ORDER BY c1.name"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_category(
        self,
        category_id: int,
        name: Optional[str] = None,
        parent_id: Optional[int] = None
    ) -> None:
        """
        Update a category.

        Args:
            category_id: ID of the category to update
            name: New category name (optional)
            parent_id: New parent category ID (optional)
        """
        logger = logging.getLogger(__name__)
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if parent_id is not None:
            updates.append("parent_id = ?")
            params.append(parent_id)

        if not updates:
            return

        query = f"""
            UPDATE categories
            SET {", ".join(updates)}
            WHERE id = ?
        """
        params.append(category_id)

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, params)
                conn.commit()
                logger.info(f"Updated category {category_id}")
        except sqlite3.Error as e:
            logger.error(f"Error updating category: {e}")
            raise

    def delete_category(self, category_id: int) -> None:
        """
        Delete a category.

        Args:
            category_id: ID of the category to delete
        """
        logger = logging.getLogger(__name__)
        query = "DELETE FROM categories WHERE id = ?"

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, (category_id,))
                conn.commit()
                logger.info(f"Deleted category {category_id}")
        except sqlite3.Error as e:
            logger.error(f"Error deleting category: {e}")
            raise

    def get_category_hierarchy(self) -> List[Dict[str, Any]]:
        """
        Get categories with their full hierarchy path.

        Returns:
            List of categories with hierarchy information
        """
        query = """
            WITH RECURSIVE category_path AS (
                -- Base case: categories without parents
                SELECT
                    id,
                    name,
                    parent_id,
                    name as path,
                    1 as level
                FROM categories
                WHERE parent_id IS NULL

                UNION ALL

                -- Recursive case: categories with parents
                SELECT
                    c.id,
                    c.name,
                    c.parent_id,
                    cp.path || ' > ' || c.name,
                    cp.level + 1
                FROM categories c
                JOIN category_path cp ON c.parent_id = cp.id
            )
            SELECT *
            FROM category_path
            ORDER BY path
        """

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
