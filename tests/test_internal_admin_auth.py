from fastapi import HTTPException

from app.core.config import Settings
from app.security import auth


def test_internal_admin_user_allows_missing_user_with_valid_internal_headers(db_session, monkeypatch):
    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: Settings(APP_ENV="production", INTERNAL_API_KEY="dev-internal-key"),
    )

    current = auth.get_internal_admin_user(
        db=db_session,
        x_internal_api_key="dev-internal-key",
        x_user_id="debug-user",
        x_user_role="admin",
    )

    assert current.user_id == "debug-user"
    assert current.role.value == "admin"


def test_get_current_user_still_requires_existing_active_user_in_production(db_session, monkeypatch):
    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: Settings(APP_ENV="production", INTERNAL_API_KEY="dev-internal-key"),
    )

    try:
        auth.get_current_user(
            db=db_session,
            x_internal_api_key="dev-internal-key",
            x_user_id="debug-user",
            x_user_role="admin",
        )
        raised = None
    except HTTPException as exc:
        raised = exc

    assert raised is not None
    assert raised.status_code == 403
    assert raised.detail == "User is not active or not found"
