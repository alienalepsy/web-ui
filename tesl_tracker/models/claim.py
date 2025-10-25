"""
Claim models

Manages TESL claims and approval workflows.
"""

import enum
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum, Text, CheckConstraint
from sqlalchemy.orm import relationship
from .base import Base


class ClaimType(enum.Enum):
    """Types of TESL claims"""
    CONFERENCE = "Conference"
    TRAINING = "Training"
    EDUCATION = "Education"
    STUDY_LEAVE = "Study Leave"
    COURSE = "Course"
    WORKSHOP = "Workshop"
    SEMINAR = "Seminar"
    OTHER = "Other"


class ClaimStatus(enum.Enum):
    """Claim status workflow"""
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    PAID = "Paid"
    CANCELLED = "Cancelled"


class ApprovalStatus(enum.Enum):
    """Individual approval status"""
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    NOT_REQUIRED = "Not Required"


class Claim(Base):
    """
    TESL Claim model

    Represents a claim for TESL funding by a staff specialist.
    """

    # Staff relationship
    staff_specialist_id = Column(Integer, ForeignKey('staff_specialist.id'),
                                 nullable=False, index=True,
                                 comment="Staff specialist making the claim")
    staff_specialist = relationship("StaffSpecialist", back_populates="claims")

    # Claim details
    claim_reference = Column(String(50), unique=True, nullable=False, index=True,
                            comment="Unique claim reference number")
    claim_type = Column(Enum(ClaimType), nullable=False,
                       comment="Type of claim")
    status = Column(Enum(ClaimStatus), nullable=False, default=ClaimStatus.DRAFT,
                   index=True, comment="Current claim status")

    # Financial details
    financial_year = Column(Integer, nullable=False, index=True,
                           comment="Financial year for this claim")
    claim_amount = Column(Float, nullable=False,
                         comment="Amount claimed")

    # Activity details
    activity_name = Column(String(255), nullable=False,
                         comment="Name of the conference/training/etc")
    activity_description = Column(Text, nullable=True,
                                 comment="Description of the activity")
    activity_start_date = Column(Date, nullable=False,
                                comment="Start date of the activity")
    activity_end_date = Column(Date, nullable=False,
                              comment="End date of the activity")
    activity_location = Column(String(255), nullable=True,
                              comment="Location of the activity")
    activity_provider = Column(String(255), nullable=True,
                              comment="Provider/organizer of the activity")

    # Supporting information
    purpose = Column(Text, nullable=True,
                    comment="Educational purpose and benefit")
    supporting_documents = Column(Text, nullable=True,
                                 comment="References to supporting documents (file paths/IDs)")

    # Expense breakdown (extensible)
    expense_registration = Column(Float, nullable=True, default=0.0,
                                 comment="Registration/enrollment fees")
    expense_travel = Column(Float, nullable=True, default=0.0,
                          comment="Travel expenses")
    expense_accommodation = Column(Float, nullable=True, default=0.0,
                              comment="Accommodation expenses")
    expense_meals = Column(Float, nullable=True, default=0.0,
                         comment="Meal allowances")
    expense_other = Column(Float, nullable=True, default=0.0,
                         comment="Other expenses")
    expense_notes = Column(Text, nullable=True,
                         comment="Notes on expenses")

    # Dates
    submitted_date = Column(Date, nullable=True,
                          comment="Date submitted for approval")
    approved_date = Column(Date, nullable=True,
                         comment="Date approved")
    paid_date = Column(Date, nullable=True,
                      comment="Date paid")

    # Payment details
    payment_reference = Column(String(100), nullable=True,
                             comment="Payment reference number")

    # Rejection/cancellation
    rejection_reason = Column(Text, nullable=True,
                            comment="Reason for rejection")
    cancelled_reason = Column(Text, nullable=True,
                            comment="Reason for cancellation")

    # Notes
    notes = Column(Text, nullable=True,
                  comment="Additional notes")

    # Relationships
    approvals = relationship("ClaimApproval", back_populates="claim",
                           cascade="all, delete-orphan",
                           order_by="ClaimApproval.approval_order")

    # Constraints
    __table_args__ = (
        CheckConstraint('claim_amount > 0', name='check_claim_amount_positive'),
        CheckConstraint('activity_end_date >= activity_start_date',
                       name='check_activity_dates'),
    )

    def __repr__(self):
        return f"<Claim(id={self.id}, ref='{self.claim_reference}', amount=${self.claim_amount:.2f}, status={self.status.value})>"

    @property
    def total_expenses(self):
        """Calculate total expenses"""
        return (
            (self.expense_registration or 0) +
            (self.expense_travel or 0) +
            (self.expense_accommodation or 0) +
            (self.expense_meals or 0) +
            (self.expense_other or 0)
        )

    @property
    def is_pending(self):
        """Check if claim is pending approval"""
        return self.status in [ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW]

    @property
    def is_approved(self):
        """Check if claim is approved"""
        return self.status in [ClaimStatus.APPROVED, ClaimStatus.PAID]

    @property
    def can_edit(self):
        """Check if claim can be edited"""
        return self.status in [ClaimStatus.DRAFT]

    @property
    def can_cancel(self):
        """Check if claim can be cancelled"""
        return self.status in [ClaimStatus.DRAFT, ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW]

    def to_dict(self):
        """Convert to dictionary with computed fields"""
        data = super().to_dict()
        data.update({
            'total_expenses': self.total_expenses,
            'is_pending': self.is_pending,
            'is_approved': self.is_approved,
            'can_edit': self.can_edit,
            'can_cancel': self.can_cancel,
            'claim_type_display': self.claim_type.value if self.claim_type else None,
            'status_display': self.status.value if self.status else None,
        })
        return data


class ClaimApproval(Base):
    """
    Claim Approval model

    Tracks the approval workflow for claims with multiple approval levels.
    """

    # Claim relationship
    claim_id = Column(Integer, ForeignKey('claim.id'),
                     nullable=False, index=True,
                     comment="Associated claim")
    claim = relationship("Claim", back_populates="approvals")

    # Approval details
    approval_level = Column(String(50), nullable=False,
                          comment="Approval level (e.g., 'supervisor', 'committee', 'finance')")
    approval_order = Column(Integer, nullable=False,
                          comment="Order in approval workflow (1, 2, 3...)")
    status = Column(Enum(ApprovalStatus), nullable=False,
                   default=ApprovalStatus.PENDING,
                   comment="Status of this approval")

    # Approver details
    approver_id = Column(Integer, ForeignKey('user.id'), nullable=True,
                        comment="User who approved/rejected")
    approver_name = Column(String(100), nullable=True,
                          comment="Name of approver (for record keeping)")
    approver_role = Column(String(50), nullable=True,
                          comment="Role of approver")

    # Approval action
    approval_date = Column(Date, nullable=True,
                         comment="Date of approval/rejection")
    comments = Column(Text, nullable=True,
                     comment="Approver comments")

    # Notification
    notification_sent = Column(Integer, default=0, nullable=False,
                             comment="Whether notification was sent (0=No, 1=Yes)")

    def __repr__(self):
        return f"<ClaimApproval(id={self.id}, claim_id={self.claim_id}, level='{self.approval_level}', status={self.status.value})>"

    @property
    def is_pending(self):
        """Check if approval is pending"""
        return self.status == ApprovalStatus.PENDING

    @property
    def is_completed(self):
        """Check if approval is completed"""
        return self.status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]
