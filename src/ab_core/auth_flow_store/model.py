from __future__ import annotations

from enum import Enum

from pydantic import AnyHttpUrl, AnyUrl, SecretStr, field_validator
from sqlalchemy import JSON, Column, String
from sqlmodel import Field, SQLModel

from ab_core.database.mixins.active import ActiveMixin
from ab_core.database.mixins.created_at import CreatedAtMixin
from ab_core.database.mixins.created_by import CreatedByMixin
from ab_core.database.mixins.id import IDMixin
from ab_core.database.mixins.updated_at import UpdatedAtMixin


class TokenIssuerType(str, Enum):
    PKCE = "pkce"
    STANDARD = "standard"


class AuthFlow(
    IDMixin,
    CreatedAtMixin,
    CreatedByMixin,
    UpdatedAtMixin,
    ActiveMixin,
    SQLModel,
    table=True,
):
    """Versioned, explicit config for a Browserless CDP-based OAuth2/OIDC flow.
    (Only first-class fields; no provider-specific extras in query params.)
    """

    # ── Issuer basics ─────────────────────────────────────────────────────────
    name: str = Field(sa_column=Column(String, nullable=False, index=True))
    issuer_type: TokenIssuerType = Field(default=TokenIssuerType.PKCE)
    identity_provider: str = Field(default="Google")
    response_type: str = Field(default="code")
    scope: str = Field(default="openid email profile")

    # ── OIDC client config ────────────────────────────────────────────────────
    client_id: str = Field(sa_column=Column(String, nullable=False))
    redirect_uri: AnyHttpUrl = Field(sa_column=Column(String, nullable=False))
    authorize_url: AnyHttpUrl = Field(sa_column=Column(String, nullable=False))
    token_url: AnyHttpUrl = Field(sa_column=Column(String, nullable=False))

    # STANDARD (confidential) clients only; we assume client_secret_basic
    client_secret: SecretStr | None = Field(default=None, sa_column=Column(String, nullable=True))

    # ── Impersonation / flow ──────────────────────────────────────────────────
    idp_prefix: AnyHttpUrl = Field(sa_column=Column(String, nullable=False))
    timeout: int = Field(default=60)

    # ── Playwright/CDP/Browserless endpoints ──────────────────────────────────
    cdp_endpoint: AnyUrl = Field(sa_column=Column(String, nullable=False))  # ws:// or wss://
    cdp_headers: dict[str, str] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    cdp_gui_base_url: AnyHttpUrl | None = Field(default=None, sa_column=Column(String, nullable=True))
    browserless_base_url: AnyHttpUrl = Field(sa_column=Column(String, nullable=False))

    # ── Validation ────────────────────────────────────────────────────────────
    @field_validator("client_secret", mode="after")
    @classmethod
    def _require_secret_for_standard(cls, v: SecretStr | None, values: dict) -> SecretStr | None:
        issuer_type: TokenIssuerType = values.get("issuer_type", TokenIssuerType.PKCE)
        if issuer_type == TokenIssuerType.STANDARD and not v:
            raise ValueError("client_secret is required when issuer_type is STANDARD")
        return v
