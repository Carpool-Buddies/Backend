"""Provider-agnostic OAuth via OpenID Connect.

Both Google and Microsoft expose OIDC discovery documents, so each provider is
just a registration entry. Adding another OIDC provider = one register() call
plus an entry in PROVIDERS.
"""
from authlib.integrations.starlette_client import OAuth

from app.core.config import get_settings

settings = get_settings()

oauth = OAuth()

# Provider codes we accept in the auth routes.
PROVIDERS = ("google", "microsoft")

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name="microsoft",
    client_id=settings.MICROSOFT_CLIENT_ID,
    client_secret=settings.MICROSOFT_CLIENT_SECRET,
    server_metadata_url=(
        f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}"
        "/v2.0/.well-known/openid-configuration"
    ),
    client_kwargs={"scope": "openid email profile"},
)


class OAuthProfile:
    """Normalized identity extracted from any provider's OIDC userinfo."""

    def __init__(self, provider: str, sub: str, email: str, name: str, picture: str | None):
        self.provider = provider
        self.sub = sub
        self.email = email
        self.name = name
        self.picture = picture


def normalize_userinfo(provider: str, userinfo: dict) -> OAuthProfile:
    """Map provider userinfo claims to our common shape.

    Standard OIDC claims (sub, email, name, picture) cover Google directly.
    Microsoft omits "picture" from userinfo, so it stays None.
    """
    email = userinfo.get("email") or userinfo.get("preferred_username") or ""
    return OAuthProfile(
        provider=provider,
        sub=str(userinfo.get("sub")),
        email=email.lower(),
        name=userinfo.get("name") or email.split("@")[0],
        picture=userinfo.get("picture"),
    )
