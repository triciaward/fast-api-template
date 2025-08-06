#!/usr/bin/env python3
"""
CLI script for managing API keys in the FastAPI template.

Usage:
    python scripts/manage_api_keys.py create --user-id <user_id> --label "My API Key" --scopes read_events write_events
    python scripts/manage_api_keys.py deactivate --key-id <key_id>
    python scripts/manage_api_keys.py list --user-id <user_id>
    python scripts/manage_api_keys.py rotate --key-id <key_id>
"""

import argparse
import sys
from datetime import datetime
from uuid import UUID

from app.crud import api_key as crud_api_key
from app.database.database import SyncSessionLocal
from app.schemas.user import APIKeyCreate

# Add the app directory to the Python path
sys.path.insert(0, ".")


def validate_uuid(uuid_string: str) -> str:
    """Validate that a string is a valid UUID."""
    try:
        UUID(uuid_string)
        return uuid_string
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"'{uuid_string}' is not a valid UUID") from e


def validate_datetime(datetime_string: str) -> datetime:
    """Validate and parse a datetime string."""
    try:
        return datetime.fromisoformat(datetime_string.replace("Z", "+00:00"))
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"'{datetime_string}' is not a valid datetime (use ISO format: YYYY-MM-DDTHH:MM:SS)"
        ) from e


def create_api_key(args: argparse.Namespace) -> None:
    """Create a new API key."""
    with SyncSessionLocal() as db:
        try:
            # Parse scopes
            scopes = args.scopes.split(",") if args.scopes else []
            scopes = [scope.strip() for scope in scopes if scope.strip()]

            # Create API key data
            api_key_data = APIKeyCreate(
                label=args.label,
                scopes=scopes,
                expires_at=args.expires_at,
            )

            # Generate the raw key first
            from app.core.security import generate_api_key

            raw_key = generate_api_key()

            # Create the API key with the raw key
            api_key = crud_api_key.create_api_key_sync(
                db=db,
                api_key_data=api_key_data,
                user_id=args.user_id,
                raw_key=raw_key,
            )

            print("✅ API key created successfully!")
            print(f"   ID: {api_key.id}")
            print(f"   Label: {api_key.label}")
            print(f"   User ID: {api_key.user_id}")
            print(
                f"   Scopes: {', '.join(api_key.scopes) if api_key.scopes else 'None'}"
            )
            print(f"   Active: {api_key.is_active}")
            print(f"   Created: {api_key.created_at}")
            if api_key.expires_at:
                print(f"   Expires: {api_key.expires_at}")

            print("\n🔑 RAW API KEY (save this securely - it won't be shown again):")
            print(f"   {raw_key}")
            print("\n⚠️  Warning: This is the only time you'll see the raw key!")

        except Exception as e:
            print(f"❌ Error creating API key: {e}")
            sys.exit(1)


def deactivate_api_key(args: argparse.Namespace) -> None:
    """Deactivate an API key."""
    with SyncSessionLocal() as db:
        try:
            success = crud_api_key.deactivate_api_key_sync(
                db=db,
                key_id=args.key_id,
                user_id=args.user_id,
            )

            if success:
                print(f"✅ API key {args.key_id} deactivated successfully!")
            else:
                print(f"❌ Failed to deactivate API key {args.key_id}")
                print("   Key not found or not owned by the specified user")
                sys.exit(1)

        except Exception as e:
            print(f"❌ Error deactivating API key: {e}")
            sys.exit(1)


def list_api_keys(args: argparse.Namespace) -> None:
    """List all API keys for a user."""
    with SyncSessionLocal() as db:
        try:
            api_keys = crud_api_key.get_user_api_keys_sync(
                db=db,
                user_id=args.user_id,
            )

            if not api_keys:
                print(f"📭 No API keys found for user {args.user_id}")
                return

            print(f"📋 API keys for user {args.user_id}:")
            print("-" * 80)

            for i, api_key in enumerate(api_keys, 1):
                status = "🟢 Active" if api_key.is_active else "🔴 Inactive"
                expired = (
                    " (Expired)"
                    if api_key.expires_at and api_key.expires_at <= datetime.utcnow()
                    else ""
                )

                print(f"{i}. {api_key.label}")
                print(f"   ID: {api_key.id}")
                print(f"   Status: {status}{expired}")
                print(
                    f"   Scopes: {', '.join(api_key.scopes) if api_key.scopes else 'None'}"
                )
                print(f"   Created: {api_key.created_at}")
                if api_key.expires_at:
                    print(f"   Expires: {api_key.expires_at}")
                print()

        except Exception as e:
            print(f"❌ Error listing API keys: {e}")
            sys.exit(1)


def rotate_api_key(args: argparse.Namespace) -> None:
    """Rotate an API key by generating a new one."""
    with SyncSessionLocal() as db:
        try:
            result = crud_api_key.rotate_api_key_sync(
                db=db,
                key_id=args.key_id,
                user_id=args.user_id,
            )

            if not result[0]:
                print(f"❌ Failed to rotate API key {args.key_id}")
                print("   Key not found or not owned by the specified user")
                sys.exit(1)

            api_key, new_raw_key = result

            # api_key is guaranteed to be not None here due to the check above
            assert api_key is not None

            print(f"✅ API key {args.key_id} rotated successfully!")
            print(f"   Label: {api_key.label}")
            print(f"   User ID: {api_key.user_id}")
            print(
                f"   Scopes: {', '.join(api_key.scopes) if api_key.scopes else 'None'}"
            )
            print(f"   Status: {'Active' if api_key.is_active else 'Inactive'}")

            print(
                "\n🔑 NEW RAW API KEY (save this securely - it won't be shown again):"
            )
            print(f"   {new_raw_key}")
            print("\n⚠️  Warning: This is the only time you'll see the new raw key!")

        except Exception as e:
            print(f"❌ Error rotating API key: {e}")
            sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Manage API keys for the FastAPI template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new API key
  python scripts/manage_api_keys.py create --user-id 123e4567-e89b-12d3-a456-426614174000 --label "My API Key" --scopes "read_events,write_events"

  # Create a key with expiration
  python scripts/manage_api_keys.py create --user-id 123e4567-e89b-12d3-a456-426614174000 --label "Temporary Key" --expires-at "2024-12-31T23:59:59"

  # Deactivate a key
  python scripts/manage_api_keys.py deactivate --key-id 123e4567-e89b-12d3-a456-426614174000

  # List all keys for a user
  python scripts/manage_api_keys.py list --user-id 123e4567-e89b-12d3-a456-426614174000

  # Rotate a key
  python scripts/manage_api_keys.py rotate --key-id 123e4567-e89b-12d3-a456-426614174000
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new API key")
    create_parser.add_argument(
        "--user-id",
        type=validate_uuid,
        required=True,
        help="User ID (UUID) to create the key for",
    )
    create_parser.add_argument(
        "--label",
        required=True,
        help="Human-readable label for the API key",
    )
    create_parser.add_argument(
        "--scopes",
        default="",
        help="Comma-separated list of scopes (e.g., 'read_events,write_events')",
    )
    create_parser.add_argument(
        "--expires-at",
        type=validate_datetime,
        help="Expiration date (ISO format: YYYY-MM-DDTHH:MM:SS)",
    )

    # Deactivate command
    deactivate_parser = subparsers.add_parser(
        "deactivate", help="Deactivate an API key"
    )
    deactivate_parser.add_argument(
        "--key-id",
        type=validate_uuid,
        required=True,
        help="API key ID to deactivate",
    )
    deactivate_parser.add_argument(
        "--user-id",
        type=validate_uuid,
        help="User ID to verify ownership (optional)",
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List all API keys for a user")
    list_parser.add_argument(
        "--user-id",
        type=validate_uuid,
        required=True,
        help="User ID to list keys for",
    )

    # Rotate command
    rotate_parser = subparsers.add_parser("rotate", help="Rotate an API key")
    rotate_parser.add_argument(
        "--key-id",
        type=validate_uuid,
        required=True,
        help="API key ID to rotate",
    )
    rotate_parser.add_argument(
        "--user-id",
        type=validate_uuid,
        help="User ID to verify ownership (optional)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute the appropriate command
    if args.command == "create":
        create_api_key(args)
    elif args.command == "deactivate":
        deactivate_api_key(args)
    elif args.command == "list":
        list_api_keys(args)
    elif args.command == "rotate":
        rotate_api_key(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
