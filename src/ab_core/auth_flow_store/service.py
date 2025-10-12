"""Auth Flow Store."""

from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .model import AuthFlow


class AuthFlowStore(BaseModel):
    """Create/read/update AuthFlow rows (flush-only, no commits)."""

    async def create(
        self,
        *,
        name: str,
        authorize_url: str,
        idp_prefix: str,
        timeout: int = 30,
        created_by: UUID | None = None,  # aligns with CreatedByMixin
        is_active: bool = True,  # aligns with ActiveMixin (is_active)
        db_session: AsyncSession,
    ) -> AuthFlow:
        row = AuthFlow(
            name=name,
            authorize_url=str(authorize_url),
            idp_prefix=str(idp_prefix),
            timeout=timeout,
            created_by=created_by,
            is_active=is_active,
        )
        db_session.add(row)
        await db_session.flush()
        return row

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
