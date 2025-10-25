"""
Audit models

Comprehensive audit logging for compliance and security.
"""

import enum
from sqlalchemy import Column, Integer, String, Text, Enum
from .base import Base


class AuditAction(enum.Enum):
    """Types of audit actions"""
    # Staff actions
    STAFF_CREATED = "Staff Created"
    STAFF_UPDATED = "Staff Updated"
    STAFF_DELETED = "Staff Deleted"
    STAFF_DEACTIVATED = "Staff Deactivated"

    # Entitlement actions
    ENTITLEMENT_CREATED = "Entitlement Created"
    ENTITLEMENT_UPDATED = "Entitlement Updated"
    ENTITLEMENT_ADJUSTED = "Entitlement Adjusted"
    YEAR_END_ROLLOVER = "Year End Rollover"

    # Claim actions
    CLAIM_CREATED = "Claim Created"
    CLAIM_UPDATED = "Claim Updated"
    CLAIM_SUBMITTED = "Claim Submitted"
    CLAIM_APPROVED = "Claim Approved"
    CLAIM_REJECTED = "Claim Rejected"
    CLAIM_PAID = "Claim Paid"
    CLAIM_CANCELLED = "Claim Cancelled"

    # User actions
    USER_LOGIN = "User Login"
    USER_LOGOUT = "User Logout"
    USER_CREATED = "User Created"
    USER_UPDATED = "User Updated"
    USER_DELETED = "User Deleted"
    USER_LOCKED = "User Locked"
    USER_UNLOCKED = "User Unlocked"
    PASSWORD_CHANGED = "Password Changed"
    PASSWORD_RESET = "Password Reset"

    # System actions
    SYSTEM_CONFIG_UPDATED = "System Config Updated"
    DATABASE_BACKUP = "Database Backup"
    DATA_IMPORT = "Data Import"
    DATA_EXPORT = "Data Export"
    REPORT_GENERATED = "Report Generated"

    # Security actions
    UNAUTHORIZED_ACCESS = "Unauthorized Access Attempt"
    PERMISSION_DENIED = "Permission Denied"
    INVALID_LOGIN = "Invalid Login Attempt"


class AuditLog(Base):
    """
    Audit Log model

    Comprehensive logging of all system activities for compliance,
    security, and troubleshooting.
    """

    # Action details
    action = Column(Enum(AuditAction), nullable=False, index=True,
                   comment="Type of action performed")
    action_description = Column(Text, nullable=False,
                               comment="Detailed description of the action")

    # User details
    user_id = Column(Integer, nullable=True, index=True,
                    comment="User who performed the action (null for system actions)")
    username = Column(String(100), nullable=True,
                     comment="Username (for record keeping)")
    user_role = Column(String(50), nullable=True,
                      comment="User role at time of action")

    # Target details
    target_type = Column(String(50), nullable=True,
                        comment="Type of entity affected (e.g., 'Staff', 'Claim')")
    target_id = Column(Integer, nullable=True,
                      comment="ID of the entity affected")
    target_description = Column(String(255), nullable=True,
                               comment="Description of the entity")

    # Change details
    old_values = Column(Text, nullable=True,
                       comment="Previous values (JSON format)")
    new_values = Column(Text, nullable=True,
                       comment="New values (JSON format)")

    # Request details
    ip_address = Column(String(45), nullable=True,
                       comment="IP address of the request")
    user_agent = Column(String(255), nullable=True,
                       comment="User agent string")

    # Status
    success = Column(Integer, default=1, nullable=False,
                    comment="Whether the action was successful (1=Yes, 0=No)")
    error_message = Column(Text, nullable=True,
                          comment="Error message if action failed")

    # Additional context
    metadata = Column(Text, nullable=True,
                     comment="Additional metadata in JSON format")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action.value}, user='{self.username}', target={self.target_type}:{self.target_id})>"

    @property
    def action_display(self):
        """Get formatted action display"""
        return self.action.value if self.action else "Unknown"

    @property
    def was_successful(self):
        """Check if action was successful"""
        return self.success == 1

    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data.update({
            'action_display': self.action_display,
            'was_successful': self.was_successful,
        })
        return data
