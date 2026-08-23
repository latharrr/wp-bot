from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api import deps as deps_module
from app.core.auth import create_access_token


@pytest.fixture
def mock_admin_repo(monkeypatch):
    mock_repo = MagicMock()
    monkeypatch.setattr(deps_module, "SupabaseAdminRepository", lambda: mock_repo)
    return mock_repo


async def _get_current_user(token: str):
    return await deps_module.get_current_user(authorization=f"Bearer {token}")


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_header():
    with pytest.raises(HTTPException) as exc:
        await deps_module.get_current_user(authorization=None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_garbage_token(mock_admin_repo):
    with pytest.raises(HTTPException) as exc:
        await _get_current_user("not-a-real-token")
    assert exc.value.status_code == 401
    mock_admin_repo.get_by_username.assert_not_called()


@pytest.mark.asyncio
async def test_get_current_user_rejects_deleted_user(mock_admin_repo):
    mock_admin_repo.get_by_username.return_value = None
    token = create_access_token("ghost")
    with pytest.raises(HTTPException) as exc:
        await _get_current_user(token)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_looks_up_role_and_features_fresh(mock_admin_repo):
    mock_admin_repo.get_by_username.return_value = {"role": "user", "allowed_features": ["groups"]}
    token = create_access_token("alice")
    user = await _get_current_user(token)
    assert user.username == "alice"
    assert user.role == "user"
    assert user.allowed_features == ["groups"]


@pytest.mark.asyncio
async def test_require_super_admin_rejects_regular_user():
    user = deps_module.CurrentUser(username="alice", role="user", allowed_features=[])
    with pytest.raises(HTTPException) as exc:
        await deps_module.require_super_admin(user=user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_super_admin_allows_super_admin():
    user = deps_module.CurrentUser(username="root", role="super_admin", allowed_features=[])
    result = await deps_module.require_super_admin(user=user)
    assert result.username == "root"


@pytest.mark.asyncio
async def test_require_feature_allows_super_admin_regardless_of_allowed_features():
    user = deps_module.CurrentUser(username="root", role="super_admin", allowed_features=[])
    check = deps_module.require_feature("csv_scoring")
    result = await check(user=user)
    assert result.username == "root"


@pytest.mark.asyncio
async def test_require_feature_allows_user_with_granted_feature():
    user = deps_module.CurrentUser(username="alice", role="user", allowed_features=["groups", "csv_scoring"])
    check = deps_module.require_feature("csv_scoring")
    result = await check(user=user)
    assert result.username == "alice"


@pytest.mark.asyncio
async def test_require_feature_rejects_user_without_granted_feature():
    user = deps_module.CurrentUser(username="alice", role="user", allowed_features=["groups"])
    check = deps_module.require_feature("csv_scoring")
    with pytest.raises(HTTPException) as exc:
        await check(user=user)
    assert exc.value.status_code == 403
