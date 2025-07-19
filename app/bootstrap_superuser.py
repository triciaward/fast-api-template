"""
Bootstrap script to create a superuser on first run.

This script checks for FIRST_SUPERUSER and FIRST_SUPERUSER_PASSWORD environment variables
and creates a superuser account if they are set and no superuser exists.
"""

import asyncio
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.user import get_user_by_email
from app.database.database import get_db
from app.schemas.user import UserCreate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_superuser(
    db: AsyncSession,
    email: str,
    password: str,
    username: Optional[str] = None
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
        username = email.split('@')[0]

    # Create superuser
    from app.crud.user import create_user

    superuser_data = UserCreate(
        email=email,
        username=username,
        password=password,
        is_superuser=True
    )

    try:
        superuser = await create_user(db, superuser_data)
        logger.info(
            f"Superuser created successfully: {superuser.email} (ID: {superuser.id})")
        return True
    except Exception as e:
        logger.error(f"Failed to create superuser: {e}")
        return False


async def bootstrap_superuser() -> None:
    """
    Bootstrap superuser if environment variables are set.
    """
    # Check if superuser environment variables are set
    if not settings.FIRST_SUPERUSER or not settings.FIRST_SUPERUSER_PASSWORD:
        logger.info(
            "FIRST_SUPERUSER or FIRST_SUPERUSER_PASSWORD not set, skipping superuser creation")
        return

    logger.info("Checking for superuser bootstrap...")

    # Get database session
    async for db in get_db():
        try:
            # Check if any superuser exists
            from sqlalchemy import select

            from app.models.models import User

            result = await db.execute(select(User).where(User.is_superuser))
            existing_superusers = result.scalars().all()

            if existing_superusers:
                logger.info(
                    f"Superuser(s) already exist: {[u.email for u in existing_superusers]}")
                return

            # Create superuser
            success = await create_superuser(
                db=db,
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD
            )

            if success:
                logger.info("Superuser bootstrap completed successfully")
            else:
                logger.warning("Superuser bootstrap failed")

        except Exception as e:
            logger.error(f"Error during superuser bootstrap: {e}")
        break


def main() -> None:
    """Main function to run the bootstrap script."""
    logger.info("Starting superuser bootstrap...")
    asyncio.run(bootstrap_superuser())
    logger.info("Superuser bootstrap completed")


if __name__ == "__main__":
    main()
