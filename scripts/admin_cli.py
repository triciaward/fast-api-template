#!/usr/bin/env python3
"""
Admin CLI utility for managing users and performing admin operations.

This script provides a command-line interface for admin operations.
"""

import argparse
import asyncio
import sys
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.admin import admin_user_crud
from app.database.database import get_db
from app.schemas.user import UserCreate


def print_json(data: dict) -> None:
    """Print data as formatted JSON."""


async def list_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    is_superuser: bool | None = None,
    is_verified: bool | None = None,
    is_deleted: bool | None = None,
    oauth_provider: str | None = None,
) -> None:
    """List users with optional filtering."""
    users = await admin_user_crud.get_users(
        db=db,
        skip=skip,
        limit=limit,
        is_superuser=is_superuser,
        is_verified=is_verified,
        is_deleted=is_deleted,
        oauth_provider=oauth_provider,
    )

    user_list = []
    for user in users:
        user_list.append(
            {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "is_superuser": user.is_superuser,
                "is_verified": user.is_verified,
                "is_deleted": user.is_deleted,
                "date_created": user.date_created,
                "oauth_provider": user.oauth_provider,
            },
        )

    print_json(
        {
            "users": user_list,
            "total": len(user_list),
            "skip": skip,
            "limit": limit,
        },
    )


async def get_user(db: AsyncSession, user_id: str) -> None:
    """Get a specific user by ID."""
    try:
        uuid_id = UUID(user_id)
    except ValueError:
        sys.exit(1)

    user = await admin_user_crud.get(db, uuid_id)
    if not user:
        sys.exit(1)

    print_json(
        {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "is_superuser": user.is_superuser,
            "is_verified": user.is_verified,
            "is_deleted": user.is_deleted,
            "date_created": user.date_created,
            "oauth_provider": user.oauth_provider,
            "oauth_id": user.oauth_id,
            "oauth_email": user.oauth_email,
            "deletion_requested_at": user.deletion_requested_at,
            "deletion_confirmed_at": user.deletion_confirmed_at,
            "deletion_scheduled_for": user.deletion_scheduled_for,
        },
    )


async def create_user(
    db: AsyncSession,
    email: str,
    username: str,
    password: str,
    is_superuser: bool = False,
    is_verified: bool = False,
) -> None:
    """Create a new user."""
    user_data = UserCreate(
        email=email,
        username=username,
        password=password,
        is_superuser=is_superuser,
    )

    try:
        user = await admin_user_crud.create_user(db, user_data)
        print_json(
            {
                "message": "User created successfully",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "is_superuser": user.is_superuser,
                    "is_verified": user.is_verified,
                },
            },
        )
    except Exception:
        sys.exit(1)


async def update_user(
    db: AsyncSession,
    user_id: str,
    email: str | None = None,
    username: str | None = None,
    password: str | None = None,
    is_superuser: bool | None = None,
    is_verified: bool | None = None,
) -> None:
    """Update a user."""
    try:
        uuid_id = UUID(user_id)
    except ValueError:
        sys.exit(1)

    from app.schemas.admin import AdminUserUpdate

    update_data: dict = {}
    if email is not None:
        update_data["email"] = email
    if username is not None:
        update_data["username"] = username
    if password is not None:
        update_data["password"] = password
    if is_superuser is not None:
        update_data["is_superuser"] = is_superuser
    if is_verified is not None:
        update_data["is_verified"] = is_verified

    user_update = AdminUserUpdate(**update_data)

    try:
        user = await admin_user_crud.update_user(db, uuid_id, user_update)
        if not user:
            sys.exit(1)

        print_json(
            {
                "message": "User updated successfully",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "is_superuser": user.is_superuser,
                    "is_verified": user.is_verified,
                },
            },
        )
    except Exception:
        sys.exit(1)


async def delete_user(db: AsyncSession, user_id: str) -> None:
    """Delete a user."""
    try:
        uuid_id = UUID(user_id)
    except ValueError:
        sys.exit(1)

    try:
        success = await admin_user_crud.delete_user(db, uuid_id)
        if success:
            print_json({"message": "User deleted successfully"})
        else:
            sys.exit(1)
    except Exception:
        sys.exit(1)


async def toggle_superuser(db: AsyncSession, user_id: str) -> None:
    """Toggle superuser status for a user."""
    try:
        uuid_id = UUID(user_id)
    except ValueError:
        sys.exit(1)

    try:
        user = await admin_user_crud.toggle_superuser_status(db, uuid_id)
        if not user:
            sys.exit(1)

        print_json(
            {
                "message": f"Superuser status {'enabled' if user.is_superuser else 'disabled'} successfully",
                "user_id": str(user.id),
                "is_superuser": user.is_superuser,
            },
        )
    except Exception:
        sys.exit(1)


async def toggle_verification(db: AsyncSession, user_id: str) -> None:
    """Toggle verification status for a user."""
    try:
        uuid_id = UUID(user_id)
    except ValueError:
        sys.exit(1)

    try:
        user = await admin_user_crud.toggle_verification_status(db, uuid_id)
        if not user:
            sys.exit(1)

        print_json(
            {
                "message": f"Verification status {'enabled' if user.is_verified else 'disabled'} successfully",
                "user_id": str(user.id),
                "is_verified": user.is_verified,
            },
        )
    except Exception:
        sys.exit(1)


async def get_statistics(db: AsyncSession) -> None:
    """Get user statistics."""
    try:
        stats = await admin_user_crud.get_user_statistics(db)
        print_json(stats)
    except Exception:
        sys.exit(1)


def main() -> None:
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Admin CLI utility")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List users command
    list_parser = subparsers.add_parser("list", help="List users")
    list_parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Number of users to skip",
    )
    list_parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of users to return",
    )
    list_parser.add_argument(
        "--superuser",
        type=bool,
        help="Filter by superuser status",
    )
    list_parser.add_argument(
        "--verified",
        type=bool,
        help="Filter by verification status",
    )
    list_parser.add_argument("--deleted", type=bool, help="Filter by deletion status")
    list_parser.add_argument(
        "--oauth-provider",
        type=str,
        help="Filter by OAuth provider",
    )

    # Get user command
    get_parser = subparsers.add_parser("get", help="Get a specific user")
    get_parser.add_argument("user_id", help="User ID")

    # Create user command
    create_parser = subparsers.add_parser("create", help="Create a new user")
    create_parser.add_argument("email", help="User email")
    create_parser.add_argument("username", help="Username")
    create_parser.add_argument("password", help="Password")
    create_parser.add_argument(
        "--superuser",
        action="store_true",
        help="Make user a superuser",
    )
    create_parser.add_argument(
        "--verified",
        action="store_true",
        help="Mark user as verified",
    )

    # Update user command
    update_parser = subparsers.add_parser("update", help="Update a user")
    update_parser.add_argument("user_id", help="User ID")
    update_parser.add_argument("--email", help="New email")
    update_parser.add_argument("--username", help="New username")
    update_parser.add_argument("--password", help="New password")
    update_parser.add_argument("--superuser", type=bool, help="Superuser status")
    update_parser.add_argument("--verified", type=bool, help="Verification status")

    # Delete user command
    delete_parser = subparsers.add_parser("delete", help="Delete a user")
    delete_parser.add_argument("user_id", help="User ID")

    # Toggle superuser command
    toggle_superuser_parser = subparsers.add_parser(
        "toggle-superuser",
        help="Toggle superuser status",
    )
    toggle_superuser_parser.add_argument("user_id", help="User ID")

    # Toggle verification command
    toggle_verification_parser = subparsers.add_parser(
        "toggle-verification",
        help="Toggle verification status",
    )
    toggle_verification_parser.add_argument("user_id", help="User ID")

    # Statistics command
    subparsers.add_parser("stats", help="Get user statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    async def run_command() -> None:
        async for db in get_db():
            try:
                if args.command == "list":
                    await list_users(
                        db=db,
                        skip=args.skip,
                        limit=args.limit,
                        is_superuser=args.superuser,
                        is_verified=args.verified,
                        is_deleted=args.deleted,
                        oauth_provider=args.oauth_provider,
                    )
                elif args.command == "get":
                    await get_user(db, args.user_id)
                elif args.command == "create":
                    await create_user(
                        db=db,
                        email=args.email,
                        username=args.username,
                        password=args.password,
                        is_superuser=args.superuser,
                        is_verified=args.verified,
                    )
                elif args.command == "update":
                    await update_user(
                        db=db,
                        user_id=args.user_id,
                        email=args.email,
                        username=args.username,
                        password=args.password,
                        is_superuser=args.superuser,
                        is_verified=args.verified,
                    )
                elif args.command == "delete":
                    await delete_user(db, args.user_id)
                elif args.command == "toggle-superuser":
                    await toggle_superuser(db, args.user_id)
                elif args.command == "toggle-verification":
                    await toggle_verification(db, args.user_id)
                elif args.command == "stats":
                    await get_statistics(db)
                break
            except Exception:
                sys.exit(1)

    asyncio.run(run_command())


if __name__ == "__main__":
    main()
