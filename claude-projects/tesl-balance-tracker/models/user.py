"""
User models

User authentication and authorization.
"""

import enum
from sqlalchemy import Column, Integer, String, Boolean, Text, Enum
from .base import Base


class UserRole(enum.Enum):
    """User roles with different permission levels"""
    EMPLOYEE = "Employee"  # Staff specialist - view own data, submit claims
    SUPERVISOR = "Supervisor"  # Manager - view team data, approve claims
    COMMITTEE_MEMBER = "Committee Member"  # No. 2 Account committee - manage Level 2-5
    FINANCE = "Finance"  # Finance officer - process payments, manage entitlements
    ADMIN = "Administrator"  # System administrator - full access


class User(Base):
    """
    User model

    Represents system users with authentication and role-based access.
    """

    # Authentication
    username = Column(String(100), unique=True, nullable=False, index=True,
                     comment="Username for login")
    email = Column(String(255), unique=True, nullable=False, index=True,
                  comment="Email address")
    password_hash = Column(String(255), nullable=True,
                          comment="Hashed password (for future authentication)")

    # Personal details
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)

    # Role and permissions
    role = Column(Enum(UserRole), nullable=False, default=UserRole.EMPLOYEE,
                 comment="User role determining permissions")

    # Link to staff specialist (if applicable)
    staff_specialist_id = Column(Integer, nullable=True,
                                comment="Linked staff specialist ID (if user is a staff member)")

    # Facility access (for supervisors/managers)
    facility_ids = Column(String(255), nullable=True,
                         comment="Comma-separated facility IDs this user can access")

    # Status
    is_active = Column(Boolean, default=True, nullable=False,
                      comment="Whether the user account is active")
    is_verified = Column(Boolean, default=False, nullable=False,
                        comment="Whether the email is verified")

    # Security
    last_login = Column(String(30), nullable=True,
                       comment="Last login timestamp")
    failed_login_attempts = Column(Integer, default=0, nullable=False,
                                  comment="Number of failed login attempts")
    account_locked = Column(Boolean, default=False, nullable=False,
                          comment="Whether the account is locked")

    # Notes
    notes = Column(Text, nullable=True,
                  comment="Administrative notes")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role={self.role.value})>"

    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self):
        """Check if user is administrator"""
        return self.role == UserRole.ADMIN

    @property
    def is_finance(self):
        """Check if user is finance officer"""
        return self.role == UserRole.FINANCE

    @property
    def is_committee_member(self):
        """Check if user is committee member"""
        return self.role == UserRole.COMMITTEE_MEMBER

    @property
    def is_supervisor(self):
        """Check if user is supervisor"""
        return self.role == UserRole.SUPERVISOR

    @property
    def can_approve_claims(self):
        """Check if user can approve claims"""
        return self.role in [UserRole.SUPERVISOR, UserRole.COMMITTEE_MEMBER, UserRole.FINANCE, UserRole.ADMIN]

    @property
    def can_manage_entitlements(self):
        """Check if user can manage entitlements"""
        return self.role in [UserRole.FINANCE, UserRole.ADMIN]

    @property
    def can_access_reports(self):
        """Check if user can access advanced reports"""
        return self.role in [UserRole.SUPERVISOR, UserRole.COMMITTEE_MEMBER, UserRole.FINANCE, UserRole.ADMIN]

    def has_facility_access(self, facility_id: int) -> bool:
        """Check if user has access to a specific facility"""
        if self.is_admin or self.is_finance:
            return True
        if not self.facility_ids:
            return False
        facility_list = [int(fid.strip()) for fid in self.facility_ids.split(',') if fid.strip()]
        return facility_id in facility_list

    def to_dict(self):
        """Convert to dictionary (excluding password)"""
        data = super().to_dict()
        data.pop('password_hash', None)  # Never expose password hash
        data.update({
            'full_name': self.full_name,
            'is_admin': self.is_admin,
            'is_finance': self.is_finance,
            'is_committee_member': self.is_committee_member,
            'is_supervisor': self.is_supervisor,
            'can_approve_claims': self.can_approve_claims,
            'can_manage_entitlements': self.can_manage_entitlements,
            'can_access_reports': self.can_access_reports,
            'role_display': self.role.value if self.role else None,
        })
        return data
