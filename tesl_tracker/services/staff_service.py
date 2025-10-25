"""
Staff Service

Manages staff specialist records.
"""

from datetime import date
from sqlalchemy.orm import Session
from typing import Optional, List

from ..models import StaffSpecialist, EmploymentScheme, StaffLevel, Facility


class StaffService:
    """Service for managing staff specialists"""

    def __init__(self, db: Session):
        self.db = db

    def create_staff(
        self,
        employee_id: str,
        first_name: str,
        last_name: str,
        email: str,
        facility_id: int,
        employment_scheme: EmploymentScheme,
        start_date: date,
        staff_level: Optional[StaffLevel] = None,
        fte: float = 1.0,
        **kwargs
    ) -> StaffSpecialist:
        """
        Create a new staff specialist

        Args:
            employee_id: Unique employee identifier
            first_name: First name
            last_name: Last name
            email: Email address
            facility_id: Facility ID
            employment_scheme: Employment scheme
            start_date: Employment start date
            staff_level: Staff level (required unless Scheme D)
            fte: Full-time equivalent (default 1.0)
            **kwargs: Additional fields

        Returns:
            StaffSpecialist: Created staff specialist
        """
        # Validate facility exists
        facility = self.db.query(Facility).get(facility_id)
        if not facility:
            raise ValueError(f"Facility {facility_id} not found")

        # Validate level for non-Scheme D staff
        if employment_scheme != EmploymentScheme.SCHEME_D and not staff_level:
            raise ValueError("Staff level required for non-Scheme D staff")

        # Determine TESL eligibility
        tesl_eligible = employment_scheme != EmploymentScheme.SCHEME_D

        staff = StaffSpecialist(
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            facility_id=facility_id,
            employment_scheme=employment_scheme,
            staff_level=staff_level,
            start_date=start_date,
            fte=fte,
            tesl_eligible=tesl_eligible,
            is_active=True,
            **kwargs
        )

        self.db.add(staff)
        self.db.flush()

        # Create initial entitlement
        from .entitlement_service import EntitlementService
        from ..utils.financial_year import get_financial_year
        ent_service = EntitlementService(self.db)
        current_fy = get_financial_year()
        ent_service.get_or_create_entitlement(staff.id, current_fy)

        return staff

    def update_staff(
        self,
        staff_id: int,
        **updates
    ) -> StaffSpecialist:
        """
        Update staff specialist details

        Args:
            staff_id: Staff specialist ID
            **updates: Fields to update

        Returns:
            StaffSpecialist: Updated staff specialist
        """
        staff = self.db.query(StaffSpecialist).get(staff_id)
        if not staff:
            raise ValueError(f"Staff specialist {staff_id} not found")

        for key, value in updates.items():
            if hasattr(staff, key):
                setattr(staff, key, value)

        self.db.flush()
        return staff

    def deactivate_staff(
        self,
        staff_id: int,
        end_date: date
    ) -> StaffSpecialist:
        """
        Deactivate a staff specialist

        Args:
            staff_id: Staff specialist ID
            end_date: Employment end date

        Returns:
            StaffSpecialist: Deactivated staff specialist
        """
        staff = self.db.query(StaffSpecialist).get(staff_id)
        if not staff:
            raise ValueError(f"Staff specialist {staff_id} not found")

        staff.is_active = False
        staff.end_date = end_date

        self.db.flush()
        return staff

    def get_staff_by_facility(
        self,
        facility_id: int,
        active_only: bool = True
    ) -> List[StaffSpecialist]:
        """
        Get all staff for a facility

        Args:
            facility_id: Facility ID
            active_only: Only return active staff (default True)

        Returns:
            List of staff specialists
        """
        query = self.db.query(StaffSpecialist).filter(
            StaffSpecialist.facility_id == facility_id
        )

        if active_only:
            query = query.filter(StaffSpecialist.is_active == True)

        return query.order_by(StaffSpecialist.last_name, StaffSpecialist.first_name).all()

    def search_staff(
        self,
        search_term: str,
        facility_id: Optional[int] = None,
        active_only: bool = True
    ) -> List[StaffSpecialist]:
        """
        Search for staff specialists

        Args:
            search_term: Search term (name, email, or employee ID)
            facility_id: Optional facility filter
            active_only: Only return active staff (default True)

        Returns:
            List of matching staff specialists
        """
        query = self.db.query(StaffSpecialist)

        # Search filter
        search_filter = (
            StaffSpecialist.first_name.ilike(f"%{search_term}%") |
            StaffSpecialist.last_name.ilike(f"%{search_term}%") |
            StaffSpecialist.email.ilike(f"%{search_term}%") |
            StaffSpecialist.employee_id.ilike(f"%{search_term}%")
        )
        query = query.filter(search_filter)

        if facility_id:
            query = query.filter(StaffSpecialist.facility_id == facility_id)

        if active_only:
            query = query.filter(StaffSpecialist.is_active == True)

        return query.order_by(StaffSpecialist.last_name, StaffSpecialist.first_name).all()
