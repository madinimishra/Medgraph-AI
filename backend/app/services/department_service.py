from app.models.department import Department
from app.repositories.department_repository import DepartmentRepository


class DepartmentService:

    @staticmethod
    def create_department(db, department):

        if DepartmentRepository.get_by_name(
            db,
            department.department_name
        ):
            raise Exception(
                "Department already exists"
            )

        new_department = Department(
            **department.model_dump()
        )

        return DepartmentRepository.create(
            db,
            new_department
        )