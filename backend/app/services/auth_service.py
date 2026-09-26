from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserRegister
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token


class AuthService:

    @staticmethod
    def register(db: Session, user: UserRegister):

        existing_user = (
            db.query(User)
            .filter(User.email == user.email)
            .first()
        )

        if existing_user:
            raise Exception("Email already registered")

        if user.role != "doctor" and user.provider_id:
            raise Exception("provider_id may only be set for the doctor role")

        new_user = User(
            full_name=user.full_name,
            email=user.email,
            password=hash_password(user.password),
            role=user.role,
            provider_id=user.provider_id
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    @staticmethod
    def login(db: Session, email: str, password: str):

        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if not user:
            return None

        if not verify_password(password, user.password):
            return None

        token = create_access_token(
            {
                "sub": user.email,
                "role": user.role,
                "provider_id": user.provider_id
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer"
        }
