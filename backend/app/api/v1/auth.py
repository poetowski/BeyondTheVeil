from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.hero import Hero
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse
from app.services.hero_service import BASELINE_STAT_VALUE, STAT_NAMES, compute_max_hp

router = APIRouter(prefix="/auth", tags=["auth"])

_invalid_credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="incorrect email or password"
)


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="email already registered")

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.flush()

    hero = Hero(
        user_id=user.id,
        name=payload.hero_name,
        **{stat: BASELINE_STAT_VALUE for stat in STAT_NAMES},
        current_hp=compute_max_hp(BASELINE_STAT_VALUE),
    )
    db.add(hero)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="email already registered") from exc

    return TokenResponse(access_token=create_access_token(subject=str(user.id)))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise _invalid_credentials_error

    return TokenResponse(access_token=create_access_token(subject=str(user.id)))
