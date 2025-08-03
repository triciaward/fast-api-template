#!/usr/bin/env python3
"""
Prevent accidental pushes to the template repository.

This script checks if the user is trying to push to the original template repository
and warns them if they haven't set up their own repository yet.
"""

import subprocess
import sys
from pathlib import Path


def get_remote_url():
    """Get the current git remote URL."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def is_template_repository(remote_url):
    """Check if the remote URL points to the template repository."""
    if not remote_url:
        return False

    # Check for common template repository patterns
    template_patterns = [
        "fast-api-template",
        "fastapi-template",
        "triciaward/fast-api-template",
        "github.com/triciaward/fast-api-template",
    ]

    return any(pattern in remote_url.lower() for pattern in template_patterns)


def main():
    """Main function to check and warn about template repository operations."""
    # Only run if we're in a git repository
    if not Path(".git").exists():
        return 0

    remote_url = get_remote_url()

    if is_template_repository(remote_url):
        print("\n" + "=" * 80)
        print("🚨 CRITICAL WARNING: Template Repository Detected!")
        print("=" * 80)
        print()
        print("You are working with the template repository!")
        print()
        print("⚠️  DANGER: Any commits or pushes could overwrite the original template")
        print("   and cause problems for others using this template.")
        print()
        print("🔧 IMMEDIATE ACTION REQUIRED:")
        print("1. Create a new GitHub repository for your project")
        print("2. Update your git remote:")
        print(
            "   git remote set-url origin https://github.com/yourusername/your-new-repo-name.git"
        )
        print("3. Then continue with your git operations")
        print()
        print("For detailed instructions, see the README.md file.")
        print("=" * 80)
        print()

        # Ask user if they want to continue anyway
        response = input("Do you want to continue with git operations anyway? (y/N): ")
        if response.lower() != "y":
            print("Git operation cancelled. Please set up your own repository first.")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
