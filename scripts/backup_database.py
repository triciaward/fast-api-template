#!/usr/bin/env python3
"""
Database backup script for production environments.

This script provides automated database backup functionality with:
- Compressed backups
- Retention policy management
- Backup verification
- Cloud storage integration (optional)
"""

import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core.config import settings
from app.core.logging_config import get_app_logger

logger = get_app_logger()


class DatabaseBackup:
    """Database backup manager for PostgreSQL."""

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

        # Parse database URL to extract connection details
        self.db_url = settings.DATABASE_URL
        self._parse_db_url()

    def _parse_db_url(self) -> None:
        """Parse database URL to extract connection parameters."""
        # Remove postgresql:// prefix
        url = self.db_url.replace("postgresql://", "")

        # Split into credentials and host/database
        if "@" in url:
            credentials, rest = url.split("@", 1)
            self.username, self.password = credentials.split(":", 1)
        else:
            self.username = "postgres"
            self.password = ""
            rest = url

        # Parse host, port, and database
        if ":" in rest:
            host_port, self.database = rest.split("/", 1)
            if ":" in host_port:
                self.host, self.port = host_port.split(":", 1)
            else:
                self.host = host_port
                self.port = "5432"
        else:
            self.host = rest.split("/")[0]
            self.port = "5432"
            self.database = rest.split("/")[1]

    def create_backup(self, compress: bool = True) -> str | None:
        """
        Create a database backup.

        Args:
            compress: Whether to compress the backup file

        Returns:
            Path to the backup file, or None if backup failed
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{self.database}_{timestamp}.sql"
        backup_path = self.backup_dir / backup_filename

        # Set environment variables for pg_dump
        env = os.environ.copy()
        env["PGPASSWORD"] = self.password

        # Build pg_dump command
        cmd = [
            "pg_dump",
            "-h",
            self.host,
            "-p",
            self.port,
            "-U",
            self.username,
            "-d",
            self.database,
            "-f",
            str(backup_path),
            "--verbose",
            "--no-password",
        ]

        try:
            logger.info(f"Starting database backup: {backup_filename}")

            # Execute backup
            subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )

            logger.info(f"Backup completed successfully: {backup_path}")

            # Compress if requested
            if compress:
                compressed_path = self._compress_backup(backup_path)
                return str(compressed_path)

            return str(backup_path)

        except subprocess.CalledProcessError as e:
            logger.exception(f"Backup failed: {e.stderr}")
            return None
        except Exception:
            logger.exception("Backup failed with unexpected error")
            return None

    def _compress_backup(self, backup_path: Path) -> Path:
        """Compress a backup file using gzip."""
        compressed_path = backup_path.with_suffix(".sql.gz")

        try:
            subprocess.run(
                ["gzip", "-f", str(backup_path)],
                check=True,
            )
            logger.info(f"Backup compressed: {compressed_path}")
            return compressed_path
        except subprocess.CalledProcessError as e:
            logger.exception(f"Compression failed: {e}")
            return backup_path

    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore a database backup.

        Args:
            backup_path: Path to the backup file

        Returns:
            True if restore was successful, False otherwise
        """
        backup_file = Path(backup_path)

        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False

        # Decompress if needed
        if backup_file.suffix == ".gz":
            backup_file = self._decompress_backup(backup_file)

        # Set environment variables for psql
        env = os.environ.copy()
        env["PGPASSWORD"] = self.password

        # Build psql command
        cmd = [
            "psql",
            "-h",
            self.host,
            "-p",
            self.port,
            "-U",
            self.username,
            "-d",
            self.database,
            "-f",
            str(backup_file),
            "--no-password",
        ]

        try:
            logger.info(f"Starting database restore from: {backup_path}")

            # Execute restore
            subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )

            logger.info("Database restore completed successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.exception(f"Restore failed: {e.stderr}")
            return False
        except Exception as e:
            logger.exception(f"Restore failed with unexpected error: {e}")
            return False

    def _decompress_backup(self, backup_path: Path) -> Path:
        """Decompress a backup file."""
        decompressed_path = backup_path.with_suffix("")

        try:
            subprocess.run(
                ["gunzip", "-f", str(backup_path)],
                check=True,
            )
            logger.info(f"Backup decompressed: {decompressed_path}")
            return decompressed_path
        except subprocess.CalledProcessError as e:
            logger.exception(f"Decompression failed: {e}")
            return backup_path

    def list_backups(self) -> list[dict]:
        """List all available backups with metadata."""
        backups = []

        for backup_file in self.backup_dir.glob("backup_*.sql*"):
            stat = backup_file.stat()
            backups.append(
                {
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created": datetime.fromtimestamp(stat.st_mtime),
                    "compressed": backup_file.suffix == ".gz",
                },
            )

        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups

    def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """
        Remove backups older than specified days.

        Args:
            days_to_keep: Number of days to keep backups

        Returns:
            Number of backups removed
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0

        for backup_file in self.backup_dir.glob("backup_*.sql*"):
            stat = backup_file.stat()
            created_date = datetime.fromtimestamp(stat.st_mtime)

            if created_date < cutoff_date:
                try:
                    backup_file.unlink()
                    logger.info(f"Removed old backup: {backup_file.name}")
                    removed_count += 1
                except Exception as e:
                    logger.exception(f"Failed to remove backup {backup_file.name}: {e}")

        logger.info(f"Cleanup completed: {removed_count} old backups removed")
        return removed_count

    def verify_backup(self, backup_path: str) -> bool:
        """
        Verify a backup file is valid.

        Args:
            backup_path: Path to the backup file

        Returns:
            True if backup is valid, False otherwise
        """
        backup_file = Path(backup_path)

        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False

        # Check file size
        if backup_file.stat().st_size == 0:
            logger.error(f"Backup file is empty: {backup_path}")
            return False

        # Check file header for SQL content
        try:
            with open(backup_file) as f:
                first_line = f.readline().strip()
                if not first_line.startswith("--") and not first_line.startswith("SET"):
                    logger.error(
                        f"Backup file doesn't appear to be valid SQL: {backup_path}",
                    )
                    return False
        except Exception as e:
            logger.exception(f"Failed to read backup file: {e}")
            return False

        logger.info(f"Backup verification passed: {backup_path}")
        return True


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Database backup utility")
    parser.add_argument(
        "action", choices=["backup", "restore", "list", "cleanup", "verify"],
    )
    parser.add_argument("--backup-dir", default="backups", help="Backup directory")
    parser.add_argument("--file", help="Backup file for restore/verify operations")
    parser.add_argument(
        "--days", type=int, default=30, help="Days to keep backups (for cleanup)",
    )
    parser.add_argument(
        "--no-compress", action="store_true", help="Don't compress backup",
    )

    args = parser.parse_args()

    backup_manager = DatabaseBackup(args.backup_dir)

    if args.action == "backup":
        backup_path = backup_manager.create_backup(compress=not args.no_compress)
        if backup_path:
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.action == "restore":
        if not args.file:
            sys.exit(1)

        success = backup_manager.restore_backup(args.file)
        if success:
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.action == "list":
        backups = backup_manager.list_backups()
        if not backups:
            pass
        else:
            for backup in backups:
                "Yes" if backup["compressed"] else "No"

    elif args.action == "cleanup":
        backup_manager.cleanup_old_backups(args.days)

    elif args.action == "verify":
        if not args.file:
            sys.exit(1)

        valid = backup_manager.verify_backup(args.file)
        if valid:
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
