"""
Data models for TESL Tracker

This module contains all SQLAlchemy ORM models for the application.
Models are designed to be extensible and maintainable.
"""

from .base import Base
from .staff import StaffSpecialist, EmploymentScheme, StaffLevel
from .entitlement import Entitlement, EntitlementHistory
from .claim import Claim, ClaimStatus, ClaimType, ClaimApproval, ApprovalStatus
from .facility import Facility, No2AccountCommittee
from .audit import AuditLog, AuditAction
from .user import User, UserRole

__all__ = [
    "Base",
    "StaffSpecialist",
    "EmploymentScheme",
    "StaffLevel",
    "Entitlement",
    "EntitlementHistory",
    "Claim",
    "ClaimStatus",
    "ClaimType",
    "ClaimApproval",
    "ApprovalStatus",
    "Facility",
    "No2AccountCommittee",
    "AuditLog",
    "AuditAction",
    "User",
    "UserRole",
]
