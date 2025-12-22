"""Base model class for SQLAlchemy ORM.

Provides the declarative base with naming conventions for constraints,
enabling Alembic autogenerate to produce consistent migration scripts.
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Naming convention for constraints enables Alembic autogenerate
# to produce consistent, predictable constraint names across migrations.
# This is essential for reliable downgrade operations.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Uses a custom MetaData with naming conventions for constraints.
    All models should inherit from this class.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
