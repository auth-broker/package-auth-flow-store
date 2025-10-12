"""Tests for AuthFlowStore."""

import uuid

import pytest

from ab_core.auth_flow_store.model import AuthFlow
from ab_core.auth_flow_store.service import AuthFlowStore


@pytest.mark.asyncio
async def test_auth_flow_store_crud(tmp_database_async_session):
    """Create, fetch, list, and flip is_active on AuthFlow rows."""
    service = AuthFlowStore()
    session = tmp_database_async_session

    # ── create ────────────────────────────────────────────────
    flow1 = await service.create(
        name="wemoney-login",
        authorize_url="https://login.wemoney.com/authorize?client_id=abc",
        idp_prefix="https://login.wemoney.com",
        timeout=45,
        created_by=uuid.uuid4(),
        is_active=True,
        db_session=session,
    )
    await session.refresh(flow1)

    assert isinstance(flow1, AuthFlow)
    assert flow1.name == "wemoney-login"
    assert flow1.authorize_url == "https://login.wemoney.com/authorize?client_id=abc"
    assert flow1.idp_prefix == "https://login.wemoney.com"
    assert flow1.timeout == 45
    assert flow1.is_active is True
    assert flow1.created_at is not None
    assert flow1.updated_at is not None

    # ── fetch by id ───────────────────────────────────────────
    fetched_by_id = await service.get_by_id(flow_id=flow1.id, db_session=session)
    assert fetched_by_id is not None
    assert fetched_by_id.id == flow1.id

    # ── fetch first by name (active only) ─────────────────────
    first_active = await service.get_by_name_first(
        name="wemoney-login",
        is_active=True,
        db_session=session,
    )
    assert first_active is not None
    assert first_active.is_active is True
    assert first_active.name == "wemoney-login"

    # ── create second flow (same name, inactive) ──────────────
    flow2 = await service.create(
        name="wemoney-login",
        authorize_url="https://login.wemoney.com/authorize?client_id=xyz",
        idp_prefix="https://login.wemoney.com",
        timeout=30,
        created_by=uuid.uuid4(),
        is_active=False,
        db_session=session,
    )
    await session.refresh(flow2)

    assert flow2.id != flow1.id
    assert flow2.is_active is False

    # ── list by name (no filter) ──────────────────────────────
    all_flows = await service.list_by_name(
        name="wemoney-login",
        db_session=session,
        is_active=None,
        limit=10,
        offset=0,
    )
    # We now have two rows with the same name
    assert isinstance(all_flows, list)
    assert len(all_flows) == 2
    assert {f.id for f in all_flows} == {flow1.id, flow2.id}

    # ── list by name (active / inactive filters) ──────────────
    active_only = await service.list_by_name(name="wemoney-login", db_session=session, is_active=True)
    inactive_only = await service.list_by_name(name="wemoney-login", db_session=session, is_active=False)
    # Exactly one active (flow1) and one inactive (flow2)
    assert {f.id for f in active_only} == {flow1.id}
    assert {f.id for f in inactive_only} == {flow2.id}

    # ── flip is_active on flow2 ───────────────────────────────
    toggled = await service.set_active(flow_id=flow2.id, is_active=True, db_session=session)
    await session.refresh(toggled)
    await session.refresh(flow1)  # refresh flow1 to read current is_active

    assert toggled is not None
    assert toggled.id == flow2.id
    assert toggled.is_active is True

    # Note: set_active flips only the specified row; others are unchanged.
    assert flow1.is_active is True  # still active (by design of the store)

    # Flip flow1 to inactive to simulate selecting flow2 as the active one
    _ = await service.set_active(flow_id=flow1.id, is_active=False, db_session=session)
    await session.refresh(flow1)

    assert flow1.is_active is False

    # Active-only should now return only flow2
    active_only_after = await service.list_by_name(name="wemoney-login", db_session=session, is_active=True)
    assert {f.id for f in active_only_after} == {flow2.id}
