"""
Entitlement Service

Manages TESL entitlement calculations, allocations, and balances.
"""

from datetime import date
from sqlalchemy.orm import Session
from typing import Optional, List

from ..models import (
    StaffSpecialist, Entitlement, EntitlementHistory,
    EmploymentScheme, Claim, ClaimStatus
)
from ..config.settings import get_config
from ..utils.financial_year import (
    get_current_financial_year,
    calculate_prorata_factor,
    get_financial_year_dates
)


class EntitlementService:
    """Service for managing TESL entitlements"""

    def __init__(self, db: Session):
        self.db = db
        self.config = get_config()

    def calculate_annual_entitlement(
        self,
        staff: StaffSpecialist,
        financial_year: int
    ) -> float:
        """
        Calculate annual TESL entitlement for a staff member

        Args:
            staff: Staff specialist
            financial_year: Financial year

        Returns:
            float: Annual entitlement amount
        """
        # Scheme D staff are not eligible for TESL
        if not staff.tesl_eligible or staff.is_scheme_d:
            return 0.0

        # Check if there's a custom entitlement
        if staff.custom_annual_entitlement is not None:
            base_amount = staff.custom_annual_entitlement
        else:
            # Use standard entitlement based on level
            base_amount = self.config.entitlements.level_1_annual_entitlement
            if staff.level_number:
                multiplier = self.config.entitlements.get_level_multiplier(staff.level_number)
                base_amount *= multiplier

        # Apply pro-rata if applicable
        prorata_factor = calculate_prorata_factor(
            start_date=staff.start_date,
            end_date=staff.end_date,
            financial_year=financial_year,
            fte=staff.fte
        )

        return round(base_amount * prorata_factor, 2)

    def get_or_create_entitlement(
        self,
        staff_id: int,
        financial_year: int
    ) -> Entitlement:
        """
        Get or create entitlement record for a staff member and financial year

        Args:
            staff_id: Staff specialist ID
            financial_year: Financial year

        Returns:
            Entitlement: Entitlement record
        """
        # Try to find existing entitlement
        entitlement = self.db.query(Entitlement).filter(
            Entitlement.staff_specialist_id == staff_id,
            Entitlement.financial_year == financial_year
        ).first()

        if entitlement:
            return entitlement

        # Create new entitlement
        staff = self.db.query(StaffSpecialist).get(staff_id)
        if not staff:
            raise ValueError(f"Staff specialist {staff_id} not found")

        annual_entitlement = self.calculate_annual_entitlement(staff, financial_year)
        max_balance = annual_entitlement * self.config.entitlements.max_accrual_years

        # Get previous year's balance for rollover
        prev_year_entitlement = self.db.query(Entitlement).filter(
            Entitlement.staff_specialist_id == staff_id,
            Entitlement.financial_year == financial_year - 1
        ).first()

        opening_balance = 0.0
        if prev_year_entitlement and prev_year_entitlement.year_end_processed:
            # Carry forward previous balance, capped at one year's entitlement
            opening_balance = min(
                prev_year_entitlement.current_balance,
                annual_entitlement
            )

        entitlement = Entitlement(
            staff_specialist_id=staff_id,
            financial_year=financial_year,
            annual_entitlement=annual_entitlement,
            opening_balance=opening_balance,
            total_entitlement=opening_balance + annual_entitlement,
            maximum_balance=max_balance,
            claimed_amount=0.0,
            pending_amount=0.0,
            current_balance=opening_balance + annual_entitlement,
            year_end_processed=0
        )

        self.db.add(entitlement)
        self.db.flush()

        # Record in history
        self._add_history(
            entitlement=entitlement,
            change_type="annual_allocation",
            description=f"Annual entitlement allocated for FY {financial_year}",
            amount=annual_entitlement,
            balance_before=opening_balance,
            balance_after=entitlement.current_balance
        )

        return entitlement

    def update_entitlement_from_claims(
        self,
        staff_id: int,
        financial_year: int
    ):
        """
        Recalculate entitlement based on current claims

        Args:
            staff_id: Staff specialist ID
            financial_year: Financial year
        """
        entitlement = self.get_or_create_entitlement(staff_id, financial_year)

        # Calculate claimed amount (approved/paid claims)
        claimed_amount = self.db.query(Claim).filter(
            Claim.staff_specialist_id == staff_id,
            Claim.financial_year == financial_year,
            Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PAID])
        ).with_entities(
            Claim.claim_amount
        ).all()
        entitlement.claimed_amount = sum(c[0] for c in claimed_amount)

        # Calculate pending amount (submitted/under review)
        pending_amount = self.db.query(Claim).filter(
            Claim.staff_specialist_id == staff_id,
            Claim.financial_year == financial_year,
            Claim.status.in_([ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW])
        ).with_entities(
            Claim.claim_amount
        ).all()
        entitlement.pending_amount = sum(c[0] for c in pending_amount)

        # Recalculate balance
        entitlement.recalculate_balance()
        self.db.flush()

    def adjust_entitlement(
        self,
        staff_id: int,
        financial_year: int,
        adjustment_amount: float,
        reason: str,
        adjusted_by: str
    ):
        """
        Make a manual adjustment to an entitlement

        Args:
            staff_id: Staff specialist ID
            financial_year: Financial year
            adjustment_amount: Amount to adjust (positive or negative)
            reason: Reason for adjustment
            adjusted_by: User making the adjustment
        """
        entitlement = self.get_or_create_entitlement(staff_id, financial_year)

        balance_before = entitlement.current_balance
        entitlement.annual_entitlement += adjustment_amount
        entitlement.recalculate_balance()
        balance_after = entitlement.current_balance

        self._add_history(
            entitlement=entitlement,
            change_type="adjustment",
            description=reason,
            amount=adjustment_amount,
            balance_before=balance_before,
            balance_after=balance_after,
            changed_by=adjusted_by
        )

        self.db.flush()

    def process_year_end_rollover(
        self,
        financial_year: int,
        processed_by: str
    ) -> int:
        """
        Process year-end rollover for all staff

        Args:
            financial_year: Financial year being closed
            processed_by: User processing the rollover

        Returns:
            int: Number of entitlements processed
        """
        entitlements = self.db.query(Entitlement).filter(
            Entitlement.financial_year == financial_year,
            Entitlement.year_end_processed == 0
        ).all()

        count = 0
        for entitlement in entitlements:
            # Mark as processed
            entitlement.year_end_processed = 1

            # Create next year's entitlement with rollover
            next_year = financial_year + 1
            self.get_or_create_entitlement(
                entitlement.staff_specialist_id,
                next_year
            )

            self._add_history(
                entitlement=entitlement,
                change_type="year_end_rollover",
                description=f"Year-end rollover to FY {next_year}",
                amount=0,
                balance_before=entitlement.current_balance,
                balance_after=entitlement.current_balance,
                changed_by=processed_by
            )

            count += 1

        self.db.flush()
        return count

    def get_staff_with_expiring_balances(
        self,
        financial_year: int,
        threshold_percentage: float = 0.9
    ) -> List[Entitlement]:
        """
        Get staff with balances at risk of expiring

        Args:
            financial_year: Financial year
            threshold_percentage: Threshold as percentage of maximum (default 90%)

        Returns:
            List of entitlements with expiring balances
        """
        return self.db.query(Entitlement).join(StaffSpecialist).filter(
            Entitlement.financial_year == financial_year,
            Entitlement.current_balance >= Entitlement.maximum_balance * threshold_percentage,
            StaffSpecialist.is_active == True
        ).all()

    def _add_history(
        self,
        entitlement: Entitlement,
        change_type: str,
        description: str,
        amount: float,
        balance_before: float,
        balance_after: float,
        changed_by: str = None,
        reference_type: str = None,
        reference_id: int = None
    ):
        """Add entry to entitlement history"""
        history = EntitlementHistory(
            entitlement_id=entitlement.id,
            change_type=change_type,
            description=description,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            changed_by=changed_by,
            reference_type=reference_type,
            reference_id=reference_id
        )
        self.db.add(history)
