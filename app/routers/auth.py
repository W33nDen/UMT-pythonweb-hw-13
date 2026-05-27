from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud
from app.auth import create_access_token, verify_password, get_email_from_verification_token
from app.database import get_db
from app.schemas import UserCreate, UserLogin, UserResponse, Token
from app.email import send_verification_email

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
    return {"access_token": access_token, "token_type": "bearer"}


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
    return {"access_token": access_token, "token_type": "bearer"}


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
