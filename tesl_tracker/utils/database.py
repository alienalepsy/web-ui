"""
Database utilities

Handles database connection, session management, and initialization.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import os

from ..config.settings import get_config
from ..models.base import Base


# Global engine and session factory
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create database engine"""
    global _engine
    if _engine is None:
        config = get_config()
        connection_string = config.database.connection_string

        # Configure engine based on database type
        if config.database.type == "sqlite":
            _engine = create_engine(
                connection_string,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False
            )
        else:
            _engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                echo=False
            )

    return _engine


def get_session_factory():
    """Get or create session factory"""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Get database session with automatic cleanup

    Usage:
        with get_db() as db:
            # Use db session
            staff = db.query(StaffSpecialist).all()
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_database(drop_existing: bool = False):
    """
    Initialize database tables

    Args:
        drop_existing: If True, drop all existing tables first
    """
    engine = get_engine()

    if drop_existing:
        Base.metadata.drop_all(bind=engine)

    # Import all models to ensure they're registered
    from ..models import (
        StaffSpecialist, Entitlement, EntitlementHistory,
        Claim, ClaimApproval, Facility, No2AccountCommittee,
        User, AuditLog
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)


def reset_database():
    """Reset database (drop and recreate all tables)"""
    init_database(drop_existing=True)


def check_database_connection() -> bool:
    """
    Check if database connection is working

    Returns:
        bool: True if connection is successful
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False
