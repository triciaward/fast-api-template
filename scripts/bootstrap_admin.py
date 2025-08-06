#!/usr/bin/env python3
"""
CLI script to bootstrap a superuser account.

Usage:
    PYTHONPATH=. python scripts/bootstrap_superuser.py
    PYTHONPATH=. python scripts/bootstrap_superuser.py --email admin@example.com --password secret123
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

from app.bootstrap_superuser import bootstrap_superuser, create_superuser
from app.database.database import get_db

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set PYTHONPATH to include the project root
os.environ["PYTHONPATH"] = str(project_root)

# Now import app modules after path is set up

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Main function for the CLI script."""
    parser = argparse.ArgumentParser(description="Bootstrap superuser account")
    parser.add_argument("--email", help="Superuser email address")
    parser.add_argument("--password", help="Superuser password")
    parser.add_argument(
        "--username",
        help="Superuser username (optional, defaults to email prefix)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force creation even if superuser already exists",
    )

    args = parser.parse_args()

    # If email and password are provided as arguments, create specific superuser
    if args.email and args.password:
        logger.info(f"Creating superuser: {args.email}")

        async for db in get_db():
            try:
                success = await create_superuser(
                    db=db,
                    email=args.email,
                    password=args.password,
                    username=args.username,
                )

                if success:
                    logger.info("Superuser created successfully!")
                else:
                    logger.warning("Superuser creation failed or user already exists")
                    if not args.force:
                        sys.exit(1)

            except Exception:
                logger.exception("Error creating superuser")
                sys.exit(1)
            break
    else:
        # Run the standard bootstrap process using environment variables
        logger.info("Running superuser bootstrap from environment variables...")
        await bootstrap_superuser()


if __name__ == "__main__":
    asyncio.run(main())
