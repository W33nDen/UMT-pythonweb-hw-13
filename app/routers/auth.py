from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud
from jose import jwt, JWTError
from app.auth import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_email_from_verification_token,
    get_email_from_password_reset_token,
    get_password_hash,
)
from app.database import get_db
from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.email import send_verification_email, send_password_reset_email
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> UserResponse:
    existing_user = crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    new_user = crud.create_user(db, user_data)
    
    # Send verification email in the background
    host = str(request.base_url)
    background_tasks.add_task(send_verification_email, new_user.email, host)

    return new_user


@router.post("/login", response_model=Token)
def login(
    user_data: UserLogin,  # Accepts separate JSON login schema
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = crud.get_user_by_email(db, user_data.email)
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Let's check if email is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified. Please verify your email first.",
        )

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    crud.update_refresh_token(db, user, refresh_token)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


# Support standard OAuth2 form login for Swagger UI / OpenAPI compatibility
@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = crud.get_user_by_email(db, form_data.username)  # Swagger passes email in the 'username' field
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified. Please verify your email first.",
        )

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    crud.update_refresh_token(db, user, refresh_token)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh_token", response_model=Token)
def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh credentials",
    )
    try:
        payload = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("scope") != "refresh_token":
            raise credentials_exception
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_email(db, email)
    if user is None or user.refresh_token != refresh_token:
        raise credentials_exception

    access_token = create_access_token(data={"sub": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.email})
    crud.update_refresh_token(db, user, new_refresh_token)

    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


@router.get("/verify/{token}")
def verify_email(token: str, db: Session = Depends(get_db)) -> dict[str, str]:
    email = get_email_from_verification_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is invalid or has expired",
        )

    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_verified:
        return {"message": "Email is already verified"}

    crud.verify_user(db, email)
    return {"message": "Email verified successfully!"}


@router.post("/request_password_reset")
async def request_password_reset(
    body: PasswordResetRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = crud.get_user_by_email(db, body.email)
    if user:
        host = str(request.base_url)
        background_tasks.add_task(send_password_reset_email, user.email, host)
    # Always return success message to prevent user enumeration
    return {"message": "If the email is registered, a password reset link has been sent."}


@router.post("/reset_password")
def reset_password(
    body: PasswordResetConfirm,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    email = get_email_from_password_reset_token(body.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token is invalid or has expired",
        )

    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    hashed_password = get_password_hash(body.new_password)
    crud.update_user_password(db, user, hashed_password)
    return {"message": "Password reset successfully!"}

