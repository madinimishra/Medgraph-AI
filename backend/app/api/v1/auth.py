from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.user import UserRegister, UserResponse, UpdateProviderLink, UpdateUserRole
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
from app.core.rbac import require_roles
from app.models.user import User
from app.graph import queries as graph_queries

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# -------------------------
# Register
# -------------------------
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    try:
        return AuthService.register(db, user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# -------------------------
# Login
# -------------------------
@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    token = AuthService.login(
        db,
        form_data.username,
        form_data.password
    )

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    return token


# -------------------------
# Current Logged-in User
# -------------------------
@router.get(
    "/me",
    response_model=UserResponse
)
def get_current_logged_in_user(
    current_user: User = Depends(get_current_user)
):
    return current_user


# -------------------------
# Admin Only
# -------------------------
@router.get("/admin")
def admin_dashboard(
    current_user: User = Depends(require_roles("admin"))
):
    return {
        "message": "Welcome Admin",
        "user": current_user.full_name,
        "role": current_user.role
    }


# -------------------------
# Doctor Only
# -------------------------
@router.get("/doctor")
def doctor_dashboard(
    current_user: User = Depends(require_roles("doctor"))
):
    return {
        "message": "Welcome Doctor",
        "user": current_user.full_name,
        "role": current_user.role
    }


# -------------------------
# Receptionist Only
# -------------------------
@router.get("/reception")
def reception_dashboard(
    current_user: User = Depends(require_roles("receptionist"))
):
    return {
        "message": "Welcome Receptionist",
        "user": current_user.full_name,
        "role": current_user.role
    }


# -------------------------
# Admin: user management (fixes the real gap where a doctor's provider
# link could previously only be set once, at registration, with no way
# to fix or add it afterward)
# -------------------------
@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    users = db.query(User).order_by(User.id).all()

    result = []
    for u in users:
        provider = graph_queries.get_provider(u.provider_id) if u.provider_id else None
        result.append({
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "provider_id": u.provider_id,
            "provider_name": provider["name"] if provider else None,
        })

    return result


@router.patch("/users/{user_id}/provider")
def update_user_provider_link(
    user_id: int,
    body: UpdateProviderLink,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != "doctor" and body.provider_id:
        raise HTTPException(
            status_code=400,
            detail="provider_id may only be set for the doctor role"
        )

    if body.provider_id and graph_queries.get_provider(body.provider_id) is None:
        raise HTTPException(status_code=400, detail="No such provider in the graph")

    user.provider_id = body.provider_id
    db.commit()
    db.refresh(user)

    provider = graph_queries.get_provider(user.provider_id) if user.provider_id else None

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "provider_id": user.provider_id,
        "provider_name": provider["name"] if provider else None,
    }


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    body: UpdateUserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You can't change your own role - ask another admin to do it"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = body.role

    if user.role != "doctor":
        user.provider_id = None

    db.commit()
    db.refresh(user)

    provider = graph_queries.get_provider(user.provider_id) if user.provider_id else None

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "provider_id": user.provider_id,
        "provider_name": provider["name"] if provider else None,
    }


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You can't delete your own account while logged in as it"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"deleted": True, "id": user_id}