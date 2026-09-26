from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class DepartmentDocument(Base):

    __tablename__ = "department_documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(255),
        nullable=False
    )

    hospital_id = Column(
        Integer,
        ForeignKey("hospital_documents.id"),
        nullable=False
    )

    hospital = relationship(
        "HospitalDocument",
        back_populates="departments"
    )

    doctors = relationship(
        "DoctorDocument",
        back_populates="department"
    )