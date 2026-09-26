from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.chat import ChatRequest, ChatResponse, CompareRequest, CompareResponse
from app.services.chat_service import ChatService
from app.services.audit_service import AuditService
from app.core.dependencies import get_current_user
from app.database.session import get_db

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


def _build_scope(current_user) -> dict:
    """Translate the authenticated user's role into a scope the
    GraphRAGAgent enforces. Fails closed: a doctor account with no
    linked provider gets no patient access rather than unrestricted
    access, and receptionists have no clinical graph-chat access at all."""

    if current_user.role == "admin":
        return None  # unrestricted

    if current_user.role == "doctor":
        if not current_user.provider_id:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Your account is not linked to a provider profile, "
                    "so patient-scoped chat access is disabled. Ask an "
                    "admin to link your account to a Provider record."
                )
            )
        return {"role": "doctor", "provider_id": current_user.provider_id}

    raise HTTPException(
        status_code=403,
        detail="Your role does not have access to the knowledge graph chat."
    )


@router.post(
    "/ask",
    response_model=ChatResponse
)
def ask_question(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    scope = _build_scope(current_user)

    try:
        result = ChatService.ask(request.question, scope=scope, advanced=request.advanced)
        AuditService.log(
            db, current_user.email, current_user.role, request.question,
            cypher=result.get("cypher"), success=True,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        AuditService.log(
            db, current_user.email, current_user.role, request.question,
            success=False, error=str(e),
        )
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post(
    "/compare",
    response_model=CompareResponse
)
def compare_question(
    request: CompareRequest,
    current_user=Depends(get_current_user)
):
    """Answers the same question via the graph-only agent and the
    vector-only agent side by side - powers the chat UI's "why graph"
    toggle. Unrestricted by RBAC scope deliberately kept simple here:
    same access rule as /ask (admin unrestricted, doctor scoped)."""

    scope = _build_scope(current_user)

    try:
        return ChatService.compare(request.question, scope=scope)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
