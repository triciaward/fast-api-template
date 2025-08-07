"""
Bootstrap script to create a superuser on first run.

This script checks for FIRST_SUPERUSER and FIRST_SUPERUSER_PASSWORD environment variables
and creates a superuser account if they are set and no superuser exists.
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.auth.user import get_user_by_email
from app.database.database import get_db
from app.schemas.auth.user import UserCreate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_superuser(
    db: AsyncSession,
    email: str,
    password: str,
    username: str | None = None,
) -> bool:
    """
    Create a superuser account.

    Args:
        db: Database session
        email: Superuser email
        password: Superuser password
        username: Optional username (defaults to email prefix)

    Returns:
        bool: True if superuser was created, False if already exists
    """
    # Check if superuser already exists
    existing_user = await get_user_by_email(db, email)
    if existing_user:
        logger.info(f"Superuser with email {email} already exists")
        return False

    # Generate username from email if not provided
    if not username:
        # Extract domain from email and create a better username
        email_prefix = email.split("@")[0]
        domain = email.split("@")[1].split(".")[0]  # Get domain without TLD
        username = f"{email_prefix}_{domain}"

        # Ensure username meets validation requirements
        if len(username) < 3:
            username = f"admin_{domain}"
        elif len(username) > 30:
            username = username[:30]

        # Replace any invalid characters
        username = username.replace(".", "_").replace("-", "_")

        # Ensure it doesn't start or end with special characters
        username = username.strip("_-")

        # If still too short, add a suffix
        if len(username) < 3:
            username = f"admin_{domain}"

        # Validate and fix username if needed
    from app.core.security import validate_username

    is_valid, error_msg = validate_username(username)
    if not is_valid:
        logger.warning(f"Generated username '{username}' is invalid: {error_msg}")
        # Try alternative username
        domain = email.split("@")[1].split(".")[0]
        username = f"admin_{domain}"
        is_valid, error_msg = validate_username(username)
        if not is_valid:
            logger.error(f"Could not generate valid username: {error_msg}")
            return False
    # Username is valid, continue

    # Validate password
    from app.core.security import validate_password

    is_valid, error_msg = validate_password(password)
    if not is_valid:
        logger.error(f"Password validation failed: {error_msg}")
        logger.info("Using default strong password: Admin123!")
        password = "Admin123!"

    # Create superuser
    from app.crud.auth.user import create_user

    superuser_data = UserCreate(
        email=email,
        username=username,
        password=password,
        is_superuser=True,
    )

    try:
        superuser = await create_user(db, superuser_data)
        logger.info(
            f"Superuser created successfully: {superuser.email} (ID: {superuser.id})",
        )
        logger.info(f"Username: {superuser.username}")
        logger.info(f"Password: {password}")
    except Exception:
        logger.exception("Failed to create superuser")
        return False
    else:
        return True


async def bootstrap_superuser() -> None:
    """
    Bootstrap superuser if environment variables are set.
    """
    # Check if superuser environment variables are set
    if not settings.FIRST_SUPERUSER or not settings.FIRST_SUPERUSER_PASSWORD:
        logger.info(
            "FIRST_SUPERUSER or FIRST_SUPERUSER_PASSWORD not set, skipping superuser creation",
        )
        return

    logger.info("Checking for superuser bootstrap...")

    # Get database session
    async for db in get_db():
        try:
            # Check if any superuser exists
            from sqlalchemy import select

            from app.models import User

            result = await db.execute(select(User).where(User.is_superuser))
            existing_superusers = result.scalars().all()

            if existing_superusers:
                logger.info(
                    f"Superuser(s) already exist: {[u.email for u in existing_superusers]}",
                )
                return

            # Create superuser
            success = await create_superuser(
                db=db,
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
            )

            if success:
                logger.info("Superuser bootstrap completed successfully")
            else:
                logger.warning("Superuser bootstrap failed")

        except Exception:
            logger.exception("Error during superuser bootstrap")
        break


def main() -> None:
    """Main function to run the bootstrap script."""
    logger.info("Starting superuser bootstrap...")
    asyncio.run(bootstrap_superuser())
    logger.info("Superuser bootstrap completed")


if __name__ == "__main__":
    main()
