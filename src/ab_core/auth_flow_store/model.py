"""ORM Model for Auth Flow."""

from pydantic import AnyHttpUrl
from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel

from ab_core.database.mixins.active import ActiveMixin
from ab_core.database.mixins.created_at import CreatedAtMixin
from ab_core.database.mixins.created_by import CreatedByMixin
from ab_core.database.mixins.id import IDMixin
from ab_core.database.mixins.updated_at import UpdatedAtMixin


class AuthFlow(
    IDMixin,
    CreatedAtMixin,
    CreatedByMixin,
    UpdatedAtMixin,
    ActiveMixin,
    SQLModel,
    table=True,
):
    """Versioned, explicit config for a Browserless CDP-based OAuth2 flow."""

    name: str = Field(sa_column=Column(String, nullable=False, index=True))
    authorize_url: AnyHttpUrl = Field(sa_column=Column(String, nullable=False))
    idp_prefix: AnyHttpUrl = Field(sa_column=Column(String, nullable=False))
    timeout: int = Field(default=30)
