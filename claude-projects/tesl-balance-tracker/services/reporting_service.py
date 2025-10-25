"""
Reporting Service

Generates reports and analytics for TESL tracking.
"""

from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List, Any
import pandas as pd

from ..models import (
    StaffSpecialist, Entitlement, Claim, ClaimStatus,
    Facility
)
from ..utils.financial_year import get_current_financial_year, format_financial_year


class ReportingService:
    """Service for generating reports and analytics"""

    def __init__(self, db: Session):
        self.db = db

    def get_staff_balance_summary(
        self,
        staff_id: int,
        financial_year: int = None
    ) -> Dict[str, Any]:
        """
        Get balance summary for a staff member

        Args:
            staff_id: Staff specialist ID
            financial_year: Financial year (defaults to current)

        Returns:
            Dictionary with balance summary
        """
        if not financial_year:
            financial_year = get_current_financial_year()

        staff = self.db.query(StaffSpecialist).get(staff_id)
        if not staff:
            raise ValueError(f"Staff specialist {staff_id} not found")

        entitlement = self.db.query(Entitlement).filter(
            Entitlement.staff_specialist_id == staff_id,
            Entitlement.financial_year == financial_year
        ).first()

        if not entitlement:
            return {
                "staff_id": staff_id,
                "staff_name": staff.full_name,
                "financial_year": financial_year,
                "financial_year_display": format_financial_year(financial_year),
                "no_entitlement": True
            }

        # Get claims summary
        claims = self.db.query(Claim).filter(
            Claim.staff_specialist_id == staff_id,
            Claim.financial_year == financial_year
        ).all()

        claims_by_status = {}
        for claim in claims:
            status = claim.status.value
            claims_by_status[status] = claims_by_status.get(status, 0) + 1

        return {
            "staff_id": staff_id,
            "staff_name": staff.full_name,
            "employee_id": staff.employee_id,
            "facility": staff.facility.facility_name if staff.facility else None,
            "financial_year": financial_year,
            "financial_year_display": format_financial_year(financial_year),
            "opening_balance": entitlement.opening_balance,
            "annual_entitlement": entitlement.annual_entitlement,
            "total_entitlement": entitlement.total_entitlement,
            "claimed_amount": entitlement.claimed_amount,
            "pending_amount": entitlement.pending_amount,
            "current_balance": entitlement.current_balance,
            "maximum_balance": entitlement.maximum_balance,
            "expiring_amount": entitlement.expiring_amount,
            "utilization_rate": entitlement.utilization_rate,
            "is_at_maximum": entitlement.is_at_maximum,
            "has_expiring_balance": entitlement.has_expiring_balance,
            "total_claims": len(claims),
            "claims_by_status": claims_by_status
        }

    def get_facility_summary(
        self,
        facility_id: int,
        financial_year: int = None
    ) -> Dict[str, Any]:
        """
        Get TESL summary for a facility

        Args:
            facility_id: Facility ID
            financial_year: Financial year (defaults to current)

        Returns:
            Dictionary with facility summary
        """
        if not financial_year:
            financial_year = get_current_financial_year()

        facility = self.db.query(Facility).get(facility_id)
        if not facility:
            raise ValueError(f"Facility {facility_id} not found")

        # Get all active staff
        staff_count = self.db.query(StaffSpecialist).filter(
            StaffSpecialist.facility_id == facility_id,
            StaffSpecialist.is_active == True
        ).count()

        # Get entitlements summary
        entitlements = self.db.query(Entitlement).join(StaffSpecialist).filter(
            StaffSpecialist.facility_id == facility_id,
            Entitlement.financial_year == financial_year
        ).all()

        total_entitlement = sum(e.total_entitlement for e in entitlements)
        total_claimed = sum(e.claimed_amount for e in entitlements)
        total_pending = sum(e.pending_amount for e in entitlements)
        total_balance = sum(e.current_balance for e in entitlements)
        total_expiring = sum(e.expiring_amount for e in entitlements)

        # Get claims summary
        claims = self.db.query(Claim).join(StaffSpecialist).filter(
            StaffSpecialist.facility_id == facility_id,
            Claim.financial_year == financial_year
        ).all()

        claims_by_status = {}
        for claim in claims:
            status = claim.status.value
            claims_by_status[status] = claims_by_status.get(status, 0) + 1

        utilization_rate = (total_claimed / total_entitlement * 100) if total_entitlement > 0 else 0

        return {
            "facility_id": facility_id,
            "facility_name": facility.facility_name,
            "facility_code": facility.facility_code,
            "financial_year": financial_year,
            "financial_year_display": format_financial_year(financial_year),
            "staff_count": staff_count,
            "total_entitlement": total_entitlement,
            "total_claimed": total_claimed,
            "total_pending": total_pending,
            "total_balance": total_balance,
            "total_expiring": total_expiring,
            "utilization_rate": round(utilization_rate, 2),
            "total_claims": len(claims),
            "claims_by_status": claims_by_status,
            "staff_with_expiring_balances": len([e for e in entitlements if e.has_expiring_balance])
        }

    def get_expiring_balances_report(
        self,
        financial_year: int = None,
        facility_id: int = None
    ) -> List[Dict[str, Any]]:
        """
        Get report of staff with expiring balances

        Args:
            financial_year: Financial year (defaults to current)
            facility_id: Optional facility filter

        Returns:
            List of staff with expiring balances
        """
        if not financial_year:
            financial_year = get_current_financial_year()

        query = self.db.query(Entitlement).join(StaffSpecialist).filter(
            Entitlement.financial_year == financial_year,
            Entitlement.expiring_amount > 0,
            StaffSpecialist.is_active == True
        )

        if facility_id:
            query = query.filter(StaffSpecialist.facility_id == facility_id)

        entitlements = query.order_by(Entitlement.expiring_amount.desc()).all()

        results = []
        for ent in entitlements:
            staff = ent.staff_specialist
            results.append({
                "staff_id": staff.id,
                "employee_id": staff.employee_id,
                "staff_name": staff.full_name,
                "facility": staff.facility.facility_name if staff.facility else None,
                "current_balance": ent.current_balance,
                "maximum_balance": ent.maximum_balance,
                "expiring_amount": ent.expiring_amount,
                "email": staff.email,
                "phone": staff.phone
            })

        return results

    def get_claims_report(
        self,
        financial_year: int = None,
        facility_id: int = None,
        status: ClaimStatus = None
    ) -> pd.DataFrame:
        """
        Get claims report as DataFrame

        Args:
            financial_year: Optional financial year filter
            facility_id: Optional facility filter
            status: Optional status filter

        Returns:
            Pandas DataFrame with claims data
        """
        query = self.db.query(Claim).join(StaffSpecialist)

        if financial_year:
            query = query.filter(Claim.financial_year == financial_year)

        if facility_id:
            query = query.filter(StaffSpecialist.facility_id == facility_id)

        if status:
            query = query.filter(Claim.status == status)

        claims = query.all()

        data = []
        for claim in claims:
            staff = claim.staff_specialist
            data.append({
                "Claim Reference": claim.claim_reference,
                "Staff Name": staff.full_name,
                "Employee ID": staff.employee_id,
                "Facility": staff.facility.facility_name if staff.facility else None,
                "Claim Type": claim.claim_type.value,
                "Activity Name": claim.activity_name,
                "Activity Date": claim.activity_start_date,
                "Claim Amount": claim.claim_amount,
                "Status": claim.status.value,
                "Submitted Date": claim.submitted_date,
                "Approved Date": claim.approved_date,
                "Paid Date": claim.paid_date
            })

        return pd.DataFrame(data)

    def get_utilization_statistics(
        self,
        financial_year: int = None
    ) -> Dict[str, Any]:
        """
        Get overall utilization statistics

        Args:
            financial_year: Financial year (defaults to current)

        Returns:
            Dictionary with utilization statistics
        """
        if not financial_year:
            financial_year = get_current_financial_year()

        entitlements = self.db.query(Entitlement).join(StaffSpecialist).filter(
            Entitlement.financial_year == financial_year,
            StaffSpecialist.is_active == True
        ).all()

        if not entitlements:
            return {
                "financial_year": financial_year,
                "no_data": True
            }

        total_staff = len(entitlements)
        total_entitlement = sum(e.total_entitlement for e in entitlements)
        total_claimed = sum(e.claimed_amount for e in entitlements)
        total_pending = sum(e.pending_amount for e in entitlements)

        staff_fully_utilized = len([e for e in entitlements if e.utilization_rate >= 90])
        staff_not_utilized = len([e for e in entitlements if e.utilization_rate == 0])
        staff_at_maximum = len([e for e in entitlements if e.is_at_maximum])

        avg_utilization = sum(e.utilization_rate for e in entitlements) / total_staff if total_staff > 0 else 0

        return {
            "financial_year": financial_year,
            "financial_year_display": format_financial_year(financial_year),
            "total_staff": total_staff,
            "total_entitlement": total_entitlement,
            "total_claimed": total_claimed,
            "total_pending": total_pending,
            "total_available": total_entitlement - total_claimed - total_pending,
            "overall_utilization_rate": (total_claimed / total_entitlement * 100) if total_entitlement > 0 else 0,
            "average_utilization_rate": avg_utilization,
            "staff_fully_utilized": staff_fully_utilized,
            "staff_not_utilized": staff_not_utilized,
            "staff_at_maximum": staff_at_maximum
        }
