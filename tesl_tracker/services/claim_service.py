"""
Claim Service

Manages TESL claim creation, updates, and workflow.
"""

from datetime import date
from sqlalchemy.orm import Session
from typing import Optional, List
import random
import string

from ..models import (
    Claim, ClaimStatus, ClaimType, ClaimApproval,
    StaffSpecialist, Entitlement
)
from ..utils.financial_year import get_financial_year


class ClaimService:
    """Service for managing TESL claims"""

    def __init__(self, db: Session):
        self.db = db

    def generate_claim_reference(self) -> str:
        """Generate unique claim reference number"""
        while True:
            # Format: TESL-YYYY-NNNN (e.g., TESL-2024-1234)
            year = date.today().year
            number = ''.join(random.choices(string.digits, k=4))
            reference = f"TESL-{year}-{number}"

            # Check if unique
            existing = self.db.query(Claim).filter(
                Claim.claim_reference == reference
            ).first()

            if not existing:
                return reference

    def create_claim(
        self,
        staff_id: int,
        claim_type: ClaimType,
        claim_amount: float,
        activity_name: str,
        activity_start_date: date,
        activity_end_date: date,
        **kwargs
    ) -> Claim:
        """
        Create a new TESL claim

        Args:
            staff_id: Staff specialist ID
            claim_type: Type of claim
            claim_amount: Amount being claimed
            activity_name: Name of the activity
            activity_start_date: Activity start date
            activity_end_date: Activity end date
            **kwargs: Additional claim fields

        Returns:
            Claim: Created claim
        """
        # Validate staff exists
        staff = self.db.query(StaffSpecialist).get(staff_id)
        if not staff:
            raise ValueError(f"Staff specialist {staff_id} not found")

        # Determine financial year
        financial_year = get_financial_year(activity_start_date)

        # Create claim
        claim = Claim(
            staff_specialist_id=staff_id,
            claim_reference=self.generate_claim_reference(),
            claim_type=claim_type,
            status=ClaimStatus.DRAFT,
            financial_year=financial_year,
            claim_amount=claim_amount,
            activity_name=activity_name,
            activity_start_date=activity_start_date,
            activity_end_date=activity_end_date,
            **kwargs
        )

        self.db.add(claim)
        self.db.flush()
        return claim

    def update_claim(
        self,
        claim_id: int,
        **updates
    ) -> Claim:
        """
        Update claim details

        Args:
            claim_id: Claim ID
            **updates: Fields to update

        Returns:
            Claim: Updated claim
        """
        claim = self.db.query(Claim).get(claim_id)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        if not claim.can_edit:
            raise ValueError("Claim cannot be edited in current status")

        for key, value in updates.items():
            if hasattr(claim, key):
                setattr(claim, key, value)

        self.db.flush()
        return claim

    def submit_claim(
        self,
        claim_id: int
    ) -> Claim:
        """
        Submit claim for approval

        Args:
            claim_id: Claim ID

        Returns:
            Claim: Submitted claim
        """
        claim = self.db.query(Claim).get(claim_id)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        if claim.status != ClaimStatus.DRAFT:
            raise ValueError("Only draft claims can be submitted")

        # Validate claim amount against available balance
        from .entitlement_service import EntitlementService
        ent_service = EntitlementService(self.db)
        entitlement = ent_service.get_or_create_entitlement(
            claim.staff_specialist_id,
            claim.financial_year
        )

        available = entitlement.current_balance - entitlement.pending_amount
        if claim.claim_amount > available:
            raise ValueError(
                f"Claim amount ${claim.claim_amount:.2f} exceeds available balance ${available:.2f}"
            )

        # Update claim status
        claim.status = ClaimStatus.SUBMITTED
        claim.submitted_date = date.today()

        # Update entitlement pending amount
        ent_service.update_entitlement_from_claims(
            claim.staff_specialist_id,
            claim.financial_year
        )

        self.db.flush()
        return claim

    def approve_claim(
        self,
        claim_id: int,
        approved_by: str
    ) -> Claim:
        """
        Approve a claim

        Args:
            claim_id: Claim ID
            approved_by: User approving the claim

        Returns:
            Claim: Approved claim
        """
        claim = self.db.query(Claim).get(claim_id)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        if not claim.is_pending:
            raise ValueError("Only pending claims can be approved")

        claim.status = ClaimStatus.APPROVED
        claim.approved_date = date.today()

        # Update entitlement
        from .entitlement_service import EntitlementService
        ent_service = EntitlementService(self.db)
        ent_service.update_entitlement_from_claims(
            claim.staff_specialist_id,
            claim.financial_year
        )

        self.db.flush()
        return claim

    def reject_claim(
        self,
        claim_id: int,
        rejection_reason: str,
        rejected_by: str
    ) -> Claim:
        """
        Reject a claim

        Args:
            claim_id: Claim ID
            rejection_reason: Reason for rejection
            rejected_by: User rejecting the claim

        Returns:
            Claim: Rejected claim
        """
        claim = self.db.query(Claim).get(claim_id)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        if not claim.is_pending:
            raise ValueError("Only pending claims can be rejected")

        claim.status = ClaimStatus.REJECTED
        claim.rejection_reason = rejection_reason

        # Update entitlement
        from .entitlement_service import EntitlementService
        ent_service = EntitlementService(self.db)
        ent_service.update_entitlement_from_claims(
            claim.staff_specialist_id,
            claim.financial_year
        )

        self.db.flush()
        return claim

    def cancel_claim(
        self,
        claim_id: int,
        cancellation_reason: str
    ) -> Claim:
        """
        Cancel a claim

        Args:
            claim_id: Claim ID
            cancellation_reason: Reason for cancellation

        Returns:
            Claim: Cancelled claim
        """
        claim = self.db.query(Claim).get(claim_id)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        if not claim.can_cancel:
            raise ValueError("Claim cannot be cancelled in current status")

        claim.status = ClaimStatus.CANCELLED
        claim.cancelled_reason = cancellation_reason

        # Update entitlement
        from .entitlement_service import EntitlementService
        ent_service = EntitlementService(self.db)
        ent_service.update_entitlement_from_claims(
            claim.staff_specialist_id,
            claim.financial_year
        )

        self.db.flush()
        return claim

    def mark_claim_paid(
        self,
        claim_id: int,
        payment_reference: str
    ) -> Claim:
        """
        Mark claim as paid

        Args:
            claim_id: Claim ID
            payment_reference: Payment reference number

        Returns:
            Claim: Paid claim
        """
        claim = self.db.query(Claim).get(claim_id)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        if claim.status != ClaimStatus.APPROVED:
            raise ValueError("Only approved claims can be marked as paid")

        claim.status = ClaimStatus.PAID
        claim.paid_date = date.today()
        claim.payment_reference = payment_reference

        self.db.flush()
        return claim

    def get_claims_for_staff(
        self,
        staff_id: int,
        financial_year: Optional[int] = None,
        status: Optional[ClaimStatus] = None
    ) -> List[Claim]:
        """
        Get claims for a staff member

        Args:
            staff_id: Staff specialist ID
            financial_year: Optional financial year filter
            status: Optional status filter

        Returns:
            List of claims
        """
        query = self.db.query(Claim).filter(
            Claim.staff_specialist_id == staff_id
        )

        if financial_year:
            query = query.filter(Claim.financial_year == financial_year)

        if status:
            query = query.filter(Claim.status == status)

        return query.order_by(Claim.created_at.desc()).all()

    def get_pending_claims(
        self,
        facility_id: Optional[int] = None
    ) -> List[Claim]:
        """
        Get all pending claims

        Args:
            facility_id: Optional facility filter

        Returns:
            List of pending claims
        """
        query = self.db.query(Claim).filter(
            Claim.status.in_([ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW])
        )

        if facility_id:
            query = query.join(StaffSpecialist).filter(
                StaffSpecialist.facility_id == facility_id
            )

        return query.order_by(Claim.submitted_date).all()
