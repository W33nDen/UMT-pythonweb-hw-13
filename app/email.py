import logging
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from app.auth import create_email_verification_token, create_password_reset_token
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize configuration only if we have settings
try:
    conf = ConnectionConfig(
        MAIL_USERNAME=settings.mail_username,
        MAIL_PASSWORD=settings.mail_password,
        MAIL_FROM=settings.mail_from or "noreply@example.com",
        MAIL_PORT=settings.mail_port,
        MAIL_SERVER=settings.mail_server,
        MAIL_FROM_NAME=settings.mail_from_name or "Contacts REST API",
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True if settings.mail_username else False,
        VALIDATE_CERTS=True,
    )
except Exception as e:
    logger.error(f"Error configuring FastAPI Mail: {e}")
    conf = None


async def send_verification_email(email: EmailStr, host: str):
    token = create_email_verification_token(email)
    verification_url = f"{host}auth/verify/{token}"

    # Print/Log verification URL to console clearly for easy local testing
    print("\n" + "=" * 80)
    print("  DEVELOPMENT VERIFICATION LINK:")
    print(f"  {verification_url}")
    print("=" * 80 + "\n")

    logger.info(f"Verification link generated: {verification_url}")

    # Fallback/Debug mode check
    is_placeholder = (
        not settings.mail_username
        or settings.mail_username == "user@example.com"
        or settings.mail_password == "secret_password"
        or not settings.mail_server
    )

    if is_placeholder or conf is None:
        logger.info("Using console fallback for verification email (placeholder/missing SMTP credentials).")
        return

    try:
        message = MessageSchema(
            subject="Confirm your email - Contacts REST API",
            recipients=[email],
            body=f"""
            <html>
                <body>
                    <p>Welcome to Contacts REST API!</p>
                    <p>Please verify your email address by clicking the link below:</p>
                    <p><a href="{verification_url}">Verify Email Address</a></p>
                    <p>Or copy and paste this URL into your browser:</p>
                    <p>{verification_url}</p>
                </body>
            </html>
            """,
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message)
        logger.info(f"Verification email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send email via SMTP: {e}. Console link is available above.")


async def send_password_reset_email(email: EmailStr, host: str):
    token = create_password_reset_token(email)
    reset_url = f"{host}auth/reset_password/{token}"

    # Print/Log reset URL to console clearly for easy local testing
    print("\n" + "=" * 80)
    print("  DEVELOPMENT PASSWORD RESET LINK:")
    print(f"  {reset_url}")
    print("=" * 80 + "\n")

    logger.info(f"Password reset link generated: {reset_url}")

    # Fallback/Debug mode check
    is_placeholder = (
        not settings.mail_username
        or settings.mail_username == "user@example.com"
        or settings.mail_password == "secret_password"
        or not settings.mail_server
    )

    if is_placeholder or conf is None:
        logger.info("Using console fallback for password reset email (placeholder/missing SMTP credentials).")
        return

    try:
        message = MessageSchema(
            subject="Reset your password - Contacts REST API",
            recipients=[email],
            body=f"""
            <html>
                <body>
                    <p>Reset your password by clicking the link below:</p>
                    <p><a href="{reset_url}">Reset Password</a></p>
                    <p>Or copy and paste this URL into your browser:</p>
                    <p>{reset_url}</p>
                </body>
            </html>
            """,
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message)
        logger.info(f"Password reset email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email via SMTP: {e}. Console link is available above.")

