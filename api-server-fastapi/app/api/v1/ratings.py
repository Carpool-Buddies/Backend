from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_session
from app.models.user import User
from app.schemas.rating import RatingCreate, RatingRead
from app.services import ratings as rating_service

router = APIRouter(tags=["ratings"])


@router.post("/rides/{ride_id}/ratings", response_model=RatingRead, status_code=status.HTTP_201_CREATED)
def rate(
    ride_id: UUID,
    data: RatingCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        rating = rating_service.create_rating(session, ride_id, user, data)
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return rating


@router.get("/users/{user_id}/ratings", response_model=list[RatingRead])
def user_ratings(
    user_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return rating_service.list_for_user(session, user_id)
