"""Authentication endpoints: signup, login, logout, password reset, me."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.email import get_email_sender
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    UserOut,
)
from app.security.passwords import hash_password, verify_password
from app.security.tokens import (
    TokenError,
    create_access_token,
    create_reset_token,
    decode_token,
)
from app.services import to_user_out

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def signup(request: Request, payload: SignupRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if _user_by_email(db, email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:  # unique race
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from exc
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id), user=to_user_out(db, user))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = _user_by_email(db, payload.email.lower())
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    return TokenResponse(access_token=create_access_token(user.id), user=to_user_out(db, user))


@router.post("/logout", response_model=MessageResponse)
def logout():
    # JWTs are stateless: "logout" is the client discarding its access token.
    return MessageResponse(message="Logged out. Discard the access token on the client.")


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("5/minute")
def forgot_password(
    request: Request, payload: ForgotPasswordRequest, db: Session = Depends(get_db)
):
    user = _user_by_email(db, payload.email.lower())
    if user is not None:
        token = create_reset_token(user.id)
        # Deep link the mobile app opens; also usable by a web reset page.
        link = f"socialcook://reset-password?token={token}"
        get_email_sender().send(
            to=user.email,
            subject="Reset your Social Cook password",
            body=(
                f"Tap to reset your password:\n{link}\n\n"
                "If you didn't request this, you can ignore this email."
            ),
        )
    # Always generic — never reveal whether an account exists for this email.
    return MessageResponse(
        message="If that email has an account, a reset link is on its way."
    )


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("5/minute")
def reset_password(
    request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)
):
    try:
        user_id = decode_token(payload.token, expected_type="reset")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        ) from exc
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )
    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    db.commit()
    return MessageResponse(message="Password updated. You can now log in.")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return to_user_out(db, user)
