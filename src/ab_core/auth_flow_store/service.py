"""Auth Flow Store (explicit kwargs, no implicit patching)."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .model import AuthFlow, TokenIssuerType


class AuthFlowStore(BaseModel):
    """Create/read/update AuthFlow rows (flush-only, no commits)."""

    # ---------------------- Create ----------------------
    async def create(
        self,
        *,
        # Issuer basics
        name: str,
        issuer_type: TokenIssuerType = TokenIssuerType.PKCE,
        identity_provider: str = "Google",
        response_type: str = "code",
        scope: str = "openid email profile",
        # OIDC client
        client_id: str,
        redirect_uri: str,
        authorize_url: str,
        token_url: str,
        client_secret: str | None = None,  # only for STANDARD clients
        # Impersonation / flow
        idp_prefix: str,
        timeout: int = 60,
        # CDP / Browserless
        cdp_endpoint: str,
        cdp_headers: dict[str, str] | None = None,
        cdp_gui_base_url: str | None = None,
        browserless_base_url: str = "",
        # Common metadata
        created_by: UUID | None = None,
        is_active: bool = True,
        db_session: AsyncSession,
    ) -> AuthFlow:
        row = AuthFlow(
            # issuer
            name=name,
            issuer_type=issuer_type,
            identity_provider=identity_provider,
            response_type=response_type,
            scope=scope,
            # client
            client_id=client_id,
            redirect_uri=redirect_uri,
            authorize_url=authorize_url,
            token_url=token_url,
            client_secret=client_secret,
            # flow
            idp_prefix=idp_prefix,
            timeout=timeout,
            # cdp
            cdp_endpoint=cdp_endpoint,
            cdp_headers=cdp_headers,
            cdp_gui_base_url=cdp_gui_base_url,
            browserless_base_url=browserless_base_url,
            # mixins
            created_by=created_by,
            is_active=is_active,
        )
        db_session.add(row)
        await db_session.flush()
        return row

    # ---------------------- Reads ----------------------
    async def get_by_id(
        self,
        *,
        flow_id: UUID,
        db_session: AsyncSession,
    ) -> AuthFlow | None:
        return await db_session.get(AuthFlow, flow_id)

    async def get_by_name_first(
        self,
        *,
        name: str,
        is_active: bool | None = None,
        db_session: AsyncSession,
    ) -> AuthFlow | None:
        """Return the first row that matches name (optionally filter by is_active)."""
        where = [AuthFlow.name == name]
        if is_active is True:
            where.append(AuthFlow.is_active.is_(True))
        elif is_active is False:
            where.append(AuthFlow.is_active.is_(False))

        stmt = select(AuthFlow).where(*where).limit(1)
        res = await db_session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_name(
        self,
        *,
        name: str,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
        db_session: AsyncSession,
    ) -> list[AuthFlow]:
        where = [AuthFlow.name == name]
        if is_active is True:
            where.append(AuthFlow.is_active.is_(True))
        elif is_active is False:
            where.append(AuthFlow.is_active.is_(False))

        stmt = select(AuthFlow).where(*where).offset(offset).limit(limit)
        res = await db_session.execute(stmt)
        return list(res.scalars())

    # ---------------------- Mutations ----------------------
    async def set_active(
        self,
        *,
        flow_id: UUID,
        is_active: bool,
        db_session: AsyncSession,
    ) -> AuthFlow | None:
        """Flip is_active for a specific row."""
        row = await db_session.get(AuthFlow, flow_id)
        if not row:
            return None
        row.is_active = is_active
        await db_session.flush()
        return row

    async def update(
        self,
        *,
        flow_id: UUID,
        # Each field is explicit and optional; only non-None values are applied.
        name: str | None = None,
        issuer_type: TokenIssuerType | None = None,
        identity_provider: str | None = None,
        response_type: str | None = None,
        scope: str | None = None,
        client_id: str | None = None,
        redirect_uri: str | None = None,
        authorize_url: str | None = None,
        token_url: str | None = None,
        client_secret: str | None = None,  # pass None to clear, omit to keep
        idp_prefix: str | None = None,
        timeout: int | None = None,
        cdp_endpoint: str | None = None,
        cdp_headers: dict[str, str] | None = None,
        cdp_gui_base_url: str | None = None,
        browserless_base_url: str | None = None,
        is_active: bool | None = None,
        db_session: AsyncSession,
    ) -> AuthFlow | None:
        """Explicit field updates only. If a parameter is None, it is NOT changed.
        Still flush-only; callers control the transaction boundary.
        """
        row = await db_session.get(AuthFlow, flow_id)
        if not row:
            return None

        if name is not None:
            row.name = name
        if issuer_type is not None:
            row.issuer_type = issuer_type
        if identity_provider is not None:
            row.identity_provider = identity_provider
        if response_type is not None:
            row.response_type = response_type
        if scope is not None:
            row.scope = scope

        if client_id is not None:
            row.client_id = client_id
        if redirect_uri is not None:
            row.redirect_uri = redirect_uri
        if authorize_url is not None:
            row.authorize_url = authorize_url
        if token_url is not None:
            row.token_url = token_url
        if client_secret is not None:
            row.client_secret = client_secret  # must be str if provided

        if idp_prefix is not None:
            row.idp_prefix = idp_prefix
        if timeout is not None:
            row.timeout = timeout

        if cdp_endpoint is not None:
            row.cdp_endpoint = cdp_endpoint
        if cdp_headers is not None:
            row.cdp_headers = cdp_headers
        if cdp_gui_base_url is not None:
            row.cdp_gui_base_url = cdp_gui_base_url
        if browserless_base_url is not None:
            row.browserless_base_url = browserless_base_url

        if is_active is not None:
            row.is_active = is_active

        await db_session.flush()
        return row
