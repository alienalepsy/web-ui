"""
Staff Specialist models

Represents NSW Health Staff Specialists and their employment details.
"""

import enum
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from .base import Base


class EmploymentScheme(enum.Enum):
    """Employment scheme types"""
    LEVEL_1 = "Level 1"
    LEVEL_2 = "Level 2"
    LEVEL_3 = "Level 3"
    LEVEL_4 = "Level 4"
    LEVEL_5 = "Level 5"
    SCHEME_D = "Scheme D"


class StaffLevel(enum.Enum):
    """Staff specialist classification levels"""
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5


class StaffSpecialist(Base):
    """
    Staff Specialist model

    Represents a staff specialist employed by NSW Health.
    Extensible design allows for adding additional fields as needed.
    """

    # Personal Information
    employee_id = Column(String(50), unique=True, nullable=False, index=True,
                        comment="Unique employee identifier")
    first_name = Column(String(100), nullable=False, comment="First name")
    last_name = Column(String(100), nullable=False, comment="Last name")
    email = Column(String(255), unique=True, nullable=False, index=True,
                  comment="Email address")
    phone = Column(String(20), nullable=True, comment="Contact phone number")

    # Employment Details
    employment_scheme = Column(Enum(EmploymentScheme), nullable=False,
                               comment="Employment scheme classification")
    staff_level = Column(Enum(StaffLevel), nullable=True,
                        comment="Staff level (None for Scheme D)")

    # FTE and dates
    fte = Column(Float, default=1.0, nullable=False,
                comment="Full-Time Equivalent (0.0-1.0)")
    start_date = Column(Date, nullable=False,
                       comment="Employment start date")
    end_date = Column(Date, nullable=True,
                     comment="Employment end date (null if active)")

    # Status
    is_active = Column(Boolean, default=True, nullable=False,
                      comment="Whether the staff member is currently active")

    # Facility relationship
    facility_id = Column(Integer, ForeignKey('facility.id'), nullable=False,
                        comment="Associated facility/hospital")
    facility = relationship("Facility", back_populates="staff_specialists")

    # TESL eligibility
    tesl_eligible = Column(Boolean, default=True, nullable=False,
                          comment="Whether eligible for TESL (False for Scheme D)")

    # Custom entitlement override (for Level 2-5 or special cases)
    custom_annual_entitlement = Column(Float, nullable=True,
                                      comment="Custom annual entitlement amount (overrides default)")

    # Additional notes (extensible field for future requirements)
    notes = Column(Text, nullable=True,
                  comment="Additional notes or comments")

    # Metadata fields (extensible JSON field for future requirements)
    # This allows adding custom fields without schema changes
    # metadata_json = Column(JSON, nullable=True, comment="Additional metadata in JSON format")

    # Relationships
    entitlements = relationship("Entitlement", back_populates="staff_specialist",
                               cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="staff_specialist",
                         cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StaffSpecialist(id={self.id}, employee_id='{self.employee_id}', name='{self.first_name} {self.last_name}')>"

    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_scheme_d(self):
        """Check if staff specialist is Scheme D"""
        return self.employment_scheme == EmploymentScheme.SCHEME_D

    @property
    def level_number(self):
        """Get level as integer (None for Scheme D)"""
        if self.staff_level:
            return self.staff_level.value
        return None

    def to_dict(self):
        """Convert to dictionary with additional computed fields"""
        data = super().to_dict()
        data.update({
            'full_name': self.full_name,
            'is_scheme_d': self.is_scheme_d,
            'level_number': self.level_number,
            'employment_scheme_display': self.employment_scheme.value if self.employment_scheme else None,
            'staff_level_display': f"Level {self.staff_level.value}" if self.staff_level else None,
        })
        return data
