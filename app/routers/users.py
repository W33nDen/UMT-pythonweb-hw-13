import logging
import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app import crud
from app.auth import get_current_user, RoleChecker
from app.config import get_settings
from app.database import get_db
from app.models import User
from app.schemas import UserResponse

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize slowapi limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/users", tags=["users"])

# Configure Cloudinary
try:
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
except Exception as e:
    logger.error(f"Error configuring Cloudinary: {e}")


@router.get("/me", response_model=UserResponse)
@limiter.limit("10/minute")
def get_current_profile(
    request: Request,  # Required by slowapi
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get the profile of the currently logged-in user.
    Rate-limited to 10 requests per minute.
    """
    return current_user


@router.patch("/avatar", response_model=UserResponse)
def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(RoleChecker(["admin"])),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Upload and update user's avatar using Cloudinary.
    """
    # Verify the uploaded file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    # Check if Cloudinary credentials are set up
    is_cloudinary_configured = (
        settings.cloudinary_name
        and settings.cloudinary_api_key
        and settings.cloudinary_api_secret
        and settings.cloudinary_name != "your_cloudinary_cloud_name"
    )

    if not is_cloudinary_configured:
        # Development fallback/mock
        logger.warning("Cloudinary is not configured. Falling back to default avatar mock.")
        mock_avatar_url = f"https://www.gravatar.com/avatar/{hash(current_user.email)}?d=retro"
        updated_user = crud.update_user_avatar(db, current_user.id, mock_avatar_url)
        return updated_user

    try:
        # Upload the file to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file.file,
            folder="contacts_api_avatars",
            public_id=f"user_{current_user.id}",
            overwrite=True,
            resource_type="image",
        )
        avatar_url = upload_result.get("secure_url")
        if not avatar_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve secure URL from Cloudinary upload",
            )

        updated_user = crud.update_user_avatar(db, current_user.id, avatar_url)
        return updated_user

    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload avatar: {str(e)}",
        )
