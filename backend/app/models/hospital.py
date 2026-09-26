from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    hospital_code = Column(
        String(20),
        unique=True,
        nullable=False
    )

    hospital_name = Column(
        String(200),
        nullable=False
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

    # -------------------------
    # Relationships
    # -------------------------

    departments = relationship(
        "Department",
        back_populates="hospital"
    )

    patients = relationship(
        "Patient",
        back_populates="hospital"
    )