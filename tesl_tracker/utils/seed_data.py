"""
Seed data script

Populates the database with sample data for testing and demonstration.
"""

from datetime import date, timedelta
from sqlalchemy.orm import Session

from ..models import (
    Facility, StaffSpecialist, EmploymentScheme, StaffLevel,
    User, UserRole, Claim, ClaimType, ClaimStatus
)
from ..services import StaffService, ClaimService, EntitlementService
from ..utils.financial_year import get_current_financial_year


def seed_facilities(db: Session):
    """Create sample facilities"""
    facilities = [
        {
            "facility_code": "RPA",
            "facility_name": "Royal Prince Alfred Hospital",
            "facility_type": "Hospital",
            "suburb": "Camperdown",
            "state": "NSW",
            "postcode": "2050",
            "local_health_district": "Sydney Local Health District",
            "phone": "02 9515 6111",
            "email": "contact@rpa.health.nsw.gov.au"
        },
        {
            "facility_code": "RNSH",
            "facility_name": "Royal North Shore Hospital",
            "facility_type": "Hospital",
            "suburb": "St Leonards",
            "state": "NSW",
            "postcode": "2065",
            "local_health_district": "Northern Sydney Local Health District",
            "phone": "02 9463 1000",
            "email": "contact@rnsh.health.nsw.gov.au"
        },
        {
            "facility_code": "LIVERPOOL",
            "facility_name": "Liverpool Hospital",
            "facility_type": "Hospital",
            "suburb": "Liverpool",
            "state": "NSW",
            "postcode": "2170",
            "local_health_district": "South Western Sydney Local Health District",
            "phone": "02 8738 3000",
            "email": "contact@liverpool.health.nsw.gov.au"
        }
    ]

    created = []
    for fac_data in facilities:
        facility = Facility(**fac_data)
        db.add(facility)
        created.append(facility)

    db.flush()
    return created


def seed_users(db: Session, facilities: list):
    """Create sample users"""
    users = [
        {
            "username": "admin",
            "email": "admin@health.nsw.gov.au",
            "first_name": "System",
            "last_name": "Administrator",
            "role": UserRole.ADMIN,
            "is_active": True,
            "is_verified": True
        },
        {
            "username": "finance",
            "email": "finance@health.nsw.gov.au",
            "first_name": "Finance",
            "last_name": "Officer",
            "role": UserRole.FINANCE,
            "is_active": True,
            "is_verified": True
        },
        {
            "username": "supervisor1",
            "email": "supervisor1@health.nsw.gov.au",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "role": UserRole.SUPERVISOR,
            "facility_ids": str(facilities[0].id),
            "is_active": True,
            "is_verified": True
        }
    ]

    created = []
    for user_data in users:
        user = User(**user_data)
        db.add(user)
        created.append(user)

    db.flush()
    return created


def seed_staff(db: Session, facilities: list):
    """Create sample staff specialists"""
    staff_service = StaffService(db)
    current_year = date.today().year

    staff_data = [
        # RPA Hospital staff
        {
            "employee_id": "SS001234",
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@health.nsw.gov.au",
            "phone": "0412 345 678",
            "facility_id": facilities[0].id,
            "employment_scheme": EmploymentScheme.LEVEL_1,
            "staff_level": StaffLevel.LEVEL_1,
            "start_date": date(current_year - 3, 7, 1),
            "fte": 1.0
        },
        {
            "employee_id": "SS001235",
            "first_name": "Emma",
            "last_name": "Wilson",
            "email": "emma.wilson@health.nsw.gov.au",
            "phone": "0423 456 789",
            "facility_id": facilities[0].id,
            "employment_scheme": EmploymentScheme.LEVEL_2,
            "staff_level": StaffLevel.LEVEL_2,
            "start_date": date(current_year - 2, 1, 15),
            "fte": 0.8
        },
        # RNSH staff
        {
            "employee_id": "SS002100",
            "first_name": "Michael",
            "last_name": "Chen",
            "email": "michael.chen@health.nsw.gov.au",
            "phone": "0434 567 890",
            "facility_id": facilities[1].id,
            "employment_scheme": EmploymentScheme.LEVEL_1,
            "staff_level": StaffLevel.LEVEL_1,
            "start_date": date(current_year - 5, 7, 1),
            "fte": 1.0
        },
        {
            "employee_id": "SS002101",
            "first_name": "Scheme D",
            "last_name": "Specialist",
            "email": "schemed.specialist@health.nsw.gov.au",
            "phone": "0445 678 901",
            "facility_id": facilities[1].id,
            "employment_scheme": EmploymentScheme.SCHEME_D,
            "staff_level": None,
            "start_date": date(current_year - 1, 7, 1),
            "fte": 1.0
        },
        # Liverpool Hospital staff
        {
            "employee_id": "SS003050",
            "first_name": "Sophia",
            "last_name": "Martinez",
            "email": "sophia.martinez@health.nsw.gov.au",
            "phone": "0456 789 012",
            "facility_id": facilities[2].id,
            "employment_scheme": EmploymentScheme.LEVEL_1,
            "staff_level": StaffLevel.LEVEL_1,
            "start_date": date(current_year, 1, 1),
            "fte": 1.0
        }
    ]

    created = []
    for staff_info in staff_data:
        staff = staff_service.create_staff(**staff_info)
        created.append(staff)

    db.flush()
    return created


def seed_claims(db: Session, staff_list: list):
    """Create sample claims"""
    claim_service = ClaimService(db)
    current_fy = get_current_financial_year()

    # Create some claims for the first staff member
    staff1 = staff_list[0]

    # Approved and paid claim
    claim1 = claim_service.create_claim(
        staff_id=staff1.id,
        claim_type=ClaimType.CONFERENCE,
        claim_amount=5000.00,
        activity_name="Australian Medical Conference 2024",
        activity_start_date=date(2024, 3, 15),
        activity_end_date=date(2024, 3, 17),
        activity_location="Sydney Convention Centre",
        activity_provider="Australian Medical Association",
        purpose="Professional development in emergency medicine",
        expense_registration=2000.00,
        expense_travel=1500.00,
        expense_accommodation=1200.00,
        expense_meals=300.00
    )
    claim_service.submit_claim(claim1.id)
    claim_service.approve_claim(claim1.id, "supervisor1")
    claim_service.mark_claim_paid(claim1.id, "PAY-2024-001")

    # Pending claim
    claim2 = claim_service.create_claim(
        staff_id=staff1.id,
        claim_type=ClaimType.TRAINING,
        claim_amount=3500.00,
        activity_name="Advanced Clinical Skills Workshop",
        activity_start_date=date(2024, 6, 1),
        activity_end_date=date(2024, 6, 3),
        activity_location="Melbourne",
        activity_provider="Royal Australian College of Physicians",
        purpose="Enhanced clinical training",
        expense_registration=2500.00,
        expense_travel=800.00,
        expense_accommodation=200.00
    )
    claim_service.submit_claim(claim2.id)

    # Draft claim
    claim3 = claim_service.create_claim(
        staff_id=staff1.id,
        claim_type=ClaimType.COURSE,
        claim_amount=2000.00,
        activity_name="Leadership in Healthcare Course",
        activity_start_date=date(2024, 9, 10),
        activity_end_date=date(2024, 9, 12),
        activity_location="Online",
        activity_provider="University of Sydney",
        purpose="Leadership development",
        expense_registration=2000.00
    )

    # Create claims for other staff
    staff3 = staff_list[2]
    claim4 = claim_service.create_claim(
        staff_id=staff3.id,
        claim_type=ClaimType.CONFERENCE,
        claim_amount=8000.00,
        activity_name="International Medical Summit",
        activity_start_date=date(2024, 4, 20),
        activity_end_date=date(2024, 4, 25),
        activity_location="Brisbane",
        activity_provider="International Medical Association",
        purpose="International best practices in patient care",
        expense_registration=3000.00,
        expense_travel=2500.00,
        expense_accommodation=2000.00,
        expense_meals=500.00
    )
    claim_service.submit_claim(claim4.id)

    db.flush()


def seed_all(db: Session):
    """Seed all sample data"""
    print("Seeding facilities...")
    facilities = seed_facilities(db)
    print(f"Created {len(facilities)} facilities")

    print("Seeding users...")
    users = seed_users(db, facilities)
    print(f"Created {len(users)} users")

    print("Seeding staff specialists...")
    staff = seed_staff(db, facilities)
    print(f"Created {len(staff)} staff specialists")

    print("Seeding claims...")
    seed_claims(db, staff)
    print("Created sample claims")

    db.commit()
    print("\nSample data seeded successfully!")
    print("\nLogin credentials:")
    print("  Admin: admin@health.nsw.gov.au")
    print("  Finance: finance@health.nsw.gov.au")
    print("  Supervisor: supervisor1@health.nsw.gov.au")
