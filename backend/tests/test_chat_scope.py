"""Tests for _build_scope, which turns a logged-in user's role into what
the GraphRAGAgent is allowed to do. This is the policy decision point for
RBAC - admin unrestricted, doctor scoped to their own linked provider (or
blocked if not linked), everyone else blocked - so it's worth testing on
its own without needing a running server."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1.chat import _build_scope


def _user(role, provider_id=None):
    return SimpleNamespace(role=role, provider_id=provider_id)


def test_admin_gets_no_scope_restriction():
    assert _build_scope(_user("admin")) is None


def test_a_linked_doctor_gets_scoped_to_their_own_provider():
    scope = _build_scope(_user("doctor", provider_id="provider-123"))
    assert scope == {"role": "doctor", "provider_id": "provider-123"}


def test_an_unlinked_doctor_is_blocked_not_given_full_access():
    # Fail closed: no linked provider means no patient access, never
    # "fall back to unrestricted".
    with pytest.raises(HTTPException) as exc_info:
        _build_scope(_user("doctor", provider_id=None))
    assert exc_info.value.status_code == 403


def test_a_receptionist_has_no_clinical_chat_access():
    with pytest.raises(HTTPException) as exc_info:
        _build_scope(_user("receptionist"))
    assert exc_info.value.status_code == 403
