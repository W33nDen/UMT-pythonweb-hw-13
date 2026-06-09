import json
import logging
import redis
from app.config import get_settings
from app.models import User

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    # Initialize redis client (synchronous, thread-safe pool)
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None


def get_cached_user(email: str) -> User | None:
    """
    Retrieve user from Redis cache if exists.
    """
    if not redis_client:
        return None
    try:
        user_data_str = redis_client.get(f"user:{email}")
        if user_data_str:
            user_dict = json.loads(user_data_str)
            # Reconstruct a detached User object
            user = User()
            for key, val in user_dict.items():
                setattr(user, key, val)
            return user
    except Exception as e:
        logger.error(f"Error getting user from Redis cache: {e}")
    return None


def cache_user(user: User) -> None:
    """
    Cache user data in Redis.
    """
    if not redis_client:
        return
    try:
        user_dict = {
            "id": user.id,
            "email": user.email,
            "password": user.password,
            "avatar": user.avatar,
            "is_verified": user.is_verified,
            "role": user.role,
            "refresh_token": user.refresh_token,
        }
        # Cache for 15 minutes (900 seconds)
        redis_client.setex(f"user:{user.email}", 900, json.dumps(user_dict))
    except Exception as e:
        logger.error(f"Error writing user to Redis cache: {e}")


def invalidate_user_cache(email: str) -> None:
    """
    Remove user from Redis cache.
    """
    if not redis_client:
        return
    try:
        redis_client.delete(f"user:{email}")
    except Exception as e:
        logger.error(f"Error deleting user from Redis cache: {e}")
