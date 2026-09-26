from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class HospitalDocument(Base):

    __tablename__ = "hospital_documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(255),
        unique=True,
        nullable=False
    )

    departments = relationship(
        "DepartmentDocument",
        back_populates="hospital"
    )

    patients = relationship(
        "PatientDocument",
        back_populates="hospital"
    )