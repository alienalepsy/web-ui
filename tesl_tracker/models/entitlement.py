"""
Entitlement models

Manages TESL entitlements, balances, and history for staff specialists.
"""

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import relationship
from .base import Base


class Entitlement(Base):
    """
    TESL Entitlement model

    Tracks annual TESL entitlements and balances for each staff specialist.
    One record per financial year per staff member.
    """

    # Staff relationship
    staff_specialist_id = Column(Integer, ForeignKey('staff_specialist.id'),
                                 nullable=False, index=True,
                                 comment="Associated staff specialist")
    staff_specialist = relationship("StaffSpecialist", back_populates="entitlements")

    # Financial year
    financial_year = Column(Integer, nullable=False, index=True,
                           comment="Financial year (e.g., 2024 for FY 2024/25)")

    # Entitlement amounts
    annual_entitlement = Column(Float, nullable=False, default=0.0,
                               comment="Annual TESL entitlement for this year")
    opening_balance = Column(Float, nullable=False, default=0.0,
                            comment="Balance carried forward from previous year")
    total_entitlement = Column(Float, nullable=False, default=0.0,
                              comment="Total available (opening + annual)")

    # Usage tracking
    claimed_amount = Column(Float, nullable=False, default=0.0,
                          comment="Total amount claimed (approved)")
    pending_amount = Column(Float, nullable=False, default=0.0,
                          comment="Total amount pending approval")
    current_balance = Column(Float, nullable=False, default=0.0,
                           comment="Available balance (total - claimed - pending)")

    # Maximum and expiry
    maximum_balance = Column(Float, nullable=False, default=0.0,
                            comment="Maximum allowed balance (2 years)")
    expiring_amount = Column(Float, nullable=False, default=0.0,
                            comment="Amount that will expire at year end")

    # Year end processing
    year_end_processed = Column(Integer, default=0, nullable=False,
                               comment="Flag indicating year-end rollover completed (0=No, 1=Yes)")

    # Notes
    notes = Column(Text, nullable=True,
                  comment="Notes or adjustments")

    # Relationships
    history = relationship("EntitlementHistory", back_populates="entitlement",
                          cascade="all, delete-orphan",
                          order_by="EntitlementHistory.created_at.desc()")

    # Constraints
    __table_args__ = (
        CheckConstraint('annual_entitlement >= 0', name='check_annual_entitlement_positive'),
        CheckConstraint('opening_balance >= 0', name='check_opening_balance_positive'),
        CheckConstraint('claimed_amount >= 0', name='check_claimed_amount_positive'),
        CheckConstraint('pending_amount >= 0', name='check_pending_amount_positive'),
        CheckConstraint('current_balance >= 0', name='check_current_balance_positive'),
    )

    def __repr__(self):
        return f"<Entitlement(id={self.id}, staff_id={self.staff_specialist_id}, FY={self.financial_year}, balance=${self.current_balance:.2f})>"

    def recalculate_balance(self):
        """Recalculate current balance based on entitlements and claims"""
        self.total_entitlement = self.opening_balance + self.annual_entitlement
        self.current_balance = self.total_entitlement - self.claimed_amount - self.pending_amount

        # Calculate expiring amount (anything over maximum)
        if self.current_balance > self.maximum_balance:
            self.expiring_amount = self.current_balance - self.maximum_balance
        else:
            self.expiring_amount = 0.0

    @property
    def utilization_rate(self):
        """Calculate utilization rate (percentage of entitlement used)"""
        if self.total_entitlement > 0:
            return (self.claimed_amount / self.total_entitlement) * 100
        return 0.0

    @property
    def is_at_maximum(self):
        """Check if balance is at or above maximum"""
        return self.current_balance >= self.maximum_balance

    @property
    def has_expiring_balance(self):
        """Check if there is an expiring balance"""
        return self.expiring_amount > 0

    def to_dict(self):
        """Convert to dictionary with computed fields"""
        data = super().to_dict()
        data.update({
            'utilization_rate': round(self.utilization_rate, 2),
            'is_at_maximum': self.is_at_maximum,
            'has_expiring_balance': self.has_expiring_balance,
        })
        return data


class EntitlementHistory(Base):
    """
    Entitlement History model

    Tracks all changes to entitlement balances for audit purposes.
    """

    # Entitlement relationship
    entitlement_id = Column(Integer, ForeignKey('entitlement.id'),
                           nullable=False, index=True,
                           comment="Associated entitlement record")
    entitlement = relationship("Entitlement", back_populates="history")

    # Change details
    change_type = Column(String(50), nullable=False,
                        comment="Type of change (e.g., 'annual_allocation', 'claim', 'adjustment')")
    description = Column(Text, nullable=False,
                        comment="Description of the change")

    # Amount changes
    amount = Column(Float, nullable=False, default=0.0,
                   comment="Amount of the change (positive or negative)")
    balance_before = Column(Float, nullable=False,
                          comment="Balance before the change")
    balance_after = Column(Float, nullable=False,
                         comment="Balance after the change")

    # Reference (e.g., claim ID, adjustment ticket)
    reference_type = Column(String(50), nullable=True,
                           comment="Type of reference (e.g., 'claim', 'adjustment')")
    reference_id = Column(Integer, nullable=True,
                         comment="ID of the referenced record")

    # User who made the change
    changed_by = Column(String(100), nullable=True,
                       comment="User who made the change")

    def __repr__(self):
        return f"<EntitlementHistory(id={self.id}, type='{self.change_type}', amount=${self.amount:.2f})>"
