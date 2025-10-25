"""
Approval Service

Manages claim approval workflows.
"""

from datetime import date
from sqlalchemy.orm import Session
from typing import List

from ..models import Claim, ClaimApproval, ApprovalStatus, User
from ..config.settings import get_config


class ApprovalService:
    """Service for managing claim approvals"""

    def __init__(self, db: Session):
        self.db = db
        self.config = get_config()

    def create_approval_workflow(
        self,
        claim: Claim
    ) -> List[ClaimApproval]:
        """
        Create approval workflow for a claim based on amount

        Args:
            claim: Claim requiring approval

        Returns:
            List of approval records created
        """
        approvals = []
        thresholds = self.config.approvals.approval_thresholds

        # Level 1: Supervisor approval (always required)
        approvals.append(ClaimApproval(
            claim_id=claim.id,
            approval_level="supervisor",
            approval_order=1,
            status=ApprovalStatus.PENDING
        ))

        # Level 2: Committee approval (for larger amounts)
        if claim.claim_amount > thresholds.get("committee", 5000):
            approvals.append(ClaimApproval(
                claim_id=claim.id,
                approval_level="committee",
                approval_order=2,
                status=ApprovalStatus.PENDING
            ))

        # Level 3: Finance approval (for large amounts)
        if claim.claim_amount > thresholds.get("finance", 10000):
            approvals.append(ClaimApproval(
                claim_id=claim.id,
                approval_level="finance",
                approval_order=3,
                status=ApprovalStatus.PENDING
            ))

        for approval in approvals:
            self.db.add(approval)

        self.db.flush()
        return approvals

    def get_pending_approvals_for_user(
        self,
        user: User
    ) -> List[ClaimApproval]:
        """
        Get pending approvals for a user based on their role

        Args:
            user: User

        Returns:
            List of pending approvals
        """
        # Map user role to approval level
        role_to_level = {
            "Supervisor": "supervisor",
            "Committee Member": "committee",
            "Finance": "finance",
            "Administrator": None  # Admins can see all
        }

        level = role_to_level.get(user.role.value)

        query = self.db.query(ClaimApproval).filter(
            ClaimApproval.status == ApprovalStatus.PENDING
        )

        if level:
            query = query.filter(ClaimApproval.approval_level == level)

        return query.order_by(ClaimApproval.created_at).all()
