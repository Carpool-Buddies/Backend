from datetime import datetime, timezone

from sqlmodel import Session, select

from app.core.universities import detect_org
from app.models.user import User
from app.services.oauth import OAuthProfile


def get_by_id(session: Session, user_id) -> User | None:
    return session.get(User, user_id)


def upsert_from_oauth(session: Session, profile: OAuthProfile) -> User:
    """Find-or-create a user from a normalized OAuth profile.

    Match on (auth_provider, provider_sub) first — the stable identity — then
    fall back to email so a user who previously signed in with another provider
    isn't duplicated. Profile fields are refreshed on every login.
    """
    user = session.exec(
        select(User).where(
            User.auth_provider == profile.provider,
            User.provider_sub == profile.sub,
        )
    ).first()

    if user is None:
        user = session.exec(select(User).where(User.email == profile.email)).first()

    org = detect_org(profile.email)

    if user is None:
        user = User(
            email=profile.email,
            full_name=profile.name,
            avatar_url=profile.picture,
            org=org,
            auth_provider=profile.provider,
            provider_sub=profile.sub,
        )
        session.add(user)
    else:
        # Refresh identity + profile on each login.
        user.auth_provider = profile.provider
        user.provider_sub = profile.sub
        user.full_name = user.full_name or profile.name
        if profile.picture:
            user.avatar_url = profile.picture
        if org and not user.org:
            user.org = org
        user.updated_at = datetime.now(timezone.utc)

    session.commit()
    session.refresh(user)
    return user
