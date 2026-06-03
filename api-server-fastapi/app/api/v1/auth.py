from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.api.v1.deps import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    get_current_user,
)
from app.core.config import get_settings
from app.core.database import get_session
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.universities import get_university
from app.models.user import User
from app.schemas.user import OnboardingUpdate, ProfileUpdate, UserRead
from app.services import users as user_service
from app.services.oauth import PROVIDERS, normalize_userinfo, oauth

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])

# Access cookie lives as long as the access token; refresh cookie longer.
_ACCESS_MAX_AGE = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
_REFRESH_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


def _set_auth_cookies(response: Response, user_id: str) -> None:
    secure = not settings.DEBUG
    response.set_cookie(
        ACCESS_COOKIE,
        create_access_token(user_id),
        max_age=_ACCESS_MAX_AGE,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        create_refresh_token(user_id),
        max_age=_REFRESH_MAX_AGE,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def _to_read(user: User) -> UserRead:
    uni = get_university(user.org)
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        org=user.org,
        org_name_he=uni.name_he if uni else None,
        onboarded=user.onboarded,
        rating_avg=user.rating_avg,
        rating_count=user.rating_count,
        created_at=user.created_at,
    )


@router.get("/{provider}/login")
async def login(provider: str, request: Request):
    if provider not in PROVIDERS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown provider")
    client = oauth.create_client(provider)
    redirect_uri = request.url_for("auth_callback", provider=provider)
    return await client.authorize_redirect(request, str(redirect_uri))


@router.get("/{provider}/callback", name="auth_callback")
async def callback(
    provider: str,
    request: Request,
    session: Session = Depends(get_session),
):
    if provider not in PROVIDERS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown provider")
    client = oauth.create_client(provider)

    try:
        token = await client.authorize_access_token(request)
    except Exception:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=oauth")

    userinfo = token.get("userinfo")
    if not userinfo:
        userinfo = await client.userinfo(token=token)

    profile = normalize_userinfo(provider, dict(userinfo))
    if not profile.email:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=no_email")

    user = user_service.upsert_from_oauth(session, profile)

    # Send first-time users to onboarding, returning users to the app.
    dest = "/onboarding" if not user.onboarded else "/dashboard"
    response = RedirectResponse(f"{settings.FRONTEND_URL}{dest}")
    _set_auth_cookies(response, str(user.id))
    return response


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return _to_read(user)


@router.post("/onboarding", response_model=UserRead)
def complete_onboarding(
    payload: OnboardingUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user.full_name = payload.full_name.strip() or user.full_name
    if payload.org is not None:
        user.org = payload.org or None
    user.onboarded = True
    session.add(user)
    session.commit()
    session.refresh(user)
    return _to_read(user)


@router.patch("/profile", response_model=UserRead)
def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if payload.full_name is not None and payload.full_name.strip():
        user.full_name = payload.full_name.strip()
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url or None
    session.add(user)
    session.commit()
    session.refresh(user)
    return _to_read(user)


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(
    user_id: str,
    _: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return _to_read(target)


@router.post("/refresh")
def refresh(request: Request, response: Response):
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No refresh token")
    payload = decode_token(token)
    if payload.get("type") != "refresh" or "sub" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    _set_auth_cookies(response, payload["sub"])
    return {"status": "ok"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")
    return {"status": "ok"}
