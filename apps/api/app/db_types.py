"""
Custom database types for cross-database compatibility.
"""

import json
from typing import Any

from sqlalchemy import TypeDecorator, String
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY


class JSONEncodedList(TypeDecorator):
    """
    Custom type that stores lists as JSON in SQLite but uses ARRAY in PostgreSQL.

    This allows tests to run with SQLite while production uses PostgreSQL arrays.
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Use native ARRAY for PostgreSQL, JSON string for others."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_ARRAY(String))
        else:
            return dialect.type_descriptor(String)

    def process_bind_param(self, value: list[str] | None, dialect) -> Any:
        """Convert list to appropriate format for database."""
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        else:
            # For SQLite and others, serialize to JSON
            return json.dumps(value)

    def process_result_value(self, value: Any, dialect) -> list[str] | None:
        """Convert database value back to list."""
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        else:
            # For SQLite and others, deserialize from JSON
            if isinstance(value, str):
                return json.loads(value)
            return value
