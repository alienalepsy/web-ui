"""
Facility models

Represents hospitals/facilities and their No. 2 Account committees.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class Facility(Base):
    """
    Facility/Hospital model

    Represents a NSW Health facility or hospital.
    """

    # Facility details
    facility_code = Column(String(50), unique=True, nullable=False, index=True,
                          comment="Unique facility code")
    facility_name = Column(String(255), nullable=False,
                          comment="Facility name")
    facility_type = Column(String(50), nullable=True,
                          comment="Type of facility (e.g., 'Hospital', 'Network')")

    # Location
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    suburb = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True, default='NSW')
    postcode = Column(String(10), nullable=True)

    # Contact
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)

    # LHD/Network
    local_health_district = Column(String(100), nullable=True,
                                  comment="Local Health District")
    network = Column(String(100), nullable=True,
                    comment="Network affiliation")

    # TESL settings for this facility
    enable_custom_entitlements = Column(Boolean, default=False, nullable=False,
                                       comment="Whether this facility uses custom entitlements for Level 2-5")

    # No. 2 Account details
    no2_account_balance = Column(Float, nullable=True,
                                comment="Current No. 2 Account balance")

    # Status
    is_active = Column(Boolean, default=True, nullable=False,
                      comment="Whether the facility is active")

    # Notes
    notes = Column(Text, nullable=True,
                  comment="Additional notes")

    # Relationships
    staff_specialists = relationship("StaffSpecialist", back_populates="facility",
                                    cascade="all, delete-orphan")
    no2_committee = relationship("No2AccountCommittee", back_populates="facility",
                                cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Facility(id={self.id}, code='{self.facility_code}', name='{self.facility_name}')>"

    @property
    def full_address(self):
        """Get formatted full address"""
        parts = [
            self.address_line1,
            self.address_line2,
            self.suburb,
            self.state,
            self.postcode
        ]
        return ', '.join(filter(None, parts))

    def to_dict(self):
        """Convert to dictionary with computed fields"""
        data = super().to_dict()
        data.update({
            'full_address': self.full_address,
        })
        return data


class No2AccountCommittee(Base):
    """
    No. 2 Account Committee model

    Represents committee members who manage Level 2-5 TESL entitlements.
    """

    # Facility relationship
    facility_id = Column(Integer, ForeignKey('facility.id'),
                        nullable=False, index=True,
                        comment="Associated facility")
    facility = relationship("Facility", back_populates="no2_committee")

    # Committee member details
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True,
                    comment="Associated user account (if applicable)")
    member_name = Column(String(100), nullable=False,
                        comment="Committee member name")
    member_email = Column(String(255), nullable=False,
                         comment="Committee member email")
    member_phone = Column(String(20), nullable=True,
                         comment="Committee member phone")

    # Role
    role = Column(String(50), nullable=True,
                 comment="Role on committee (e.g., 'Chair', 'Member', 'Secretary')")

    # Status
    is_active = Column(Boolean, default=True, nullable=False,
                      comment="Whether the member is currently active")
    is_contributor = Column(Boolean, default=False, nullable=False,
                          comment="Whether the member is a contributor to the No. 2 Account")

    # Appointment dates
    appointment_date = Column(String(10), nullable=True,
                            comment="Date appointed to committee")
    termination_date = Column(String(10), nullable=True,
                            comment="Date membership ended")

    # Notes
    notes = Column(Text, nullable=True,
                  comment="Additional notes")

    def __repr__(self):
        return f"<No2AccountCommittee(id={self.id}, facility_id={self.facility_id}, member='{self.member_name}')>"
