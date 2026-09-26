from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Boolean,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Patient(Base):
    __tablename__ = "patients"

    # -------------------------
    # Relationships
    # -------------------------

    appointments = relationship(
        "Appointment",
        back_populates="patient"
    )

    hospital = relationship(
        "Hospital",
        back_populates="patients"
    )

    medical_records = relationship(
        "MedicalRecord",
        back_populates="patient"
    )

    # -------------------------
    # Columns
    # -------------------------

    id = Column(Integer, primary_key=True, index=True)
    
    hospital_id = Column(
    Integer,
    ForeignKey("hospitals.id"),
    nullable=False
    )
    
    patient_code = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )

    first_name = Column(
        String(100),
        nullable=False
    )

    middle_name = Column(
        String(100),
        nullable=True
    )

    last_name = Column(
        String(100),
        nullable=False
    )

    gender = Column(
        String(20),
        nullable=False
    )

    date_of_birth = Column(
        Date,
        nullable=False
    )

    phone = Column(
        String(15),
        unique=True,
        nullable=False
    )

    alternate_phone = Column(
        String(15),
        nullable=True
    )

    email = Column(
        String(150),
        unique=True,
        nullable=False
    )

    blood_group = Column(
        String(10),
        nullable=True
    )

    address = Column(
        String(300),
        nullable=False
    )

    city = Column(
        String(100),
        nullable=False
    )

    state = Column(
        String(100),
        nullable=False
    )

    country = Column(
        String(100),
        nullable=False
    )

    postal_code = Column(
        String(20),
        nullable=False
    )

    emergency_contact_name = Column(
        String(100),
        nullable=False
    )

    emergency_contact_phone = Column(
        String(15),
        nullable=False
    )

    emergency_contact_relation = Column(
        String(50),
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )