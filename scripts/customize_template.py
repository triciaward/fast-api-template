#!/usr/bin/env python3
"""
FastAPI Template Customization Script - Step 2

This script transforms the FastAPI template into a custom project by replacing
all template-specific references with user-provided project details.

IMPORTANT: This script should be run AFTER you have:
1. Renamed the template directory using rename_template.sh
2. Restarted VS Code and opened the renamed directory

Usage:
    python scripts/customize_template.py
    # or
    ./scripts/customize_template.py

The script will prompt for:
- Project name (e.g., "My Awesome Project")
- Project slug (e.g., "myawesomeproject_backend")
- Database name (e.g., "myawesomeproject_backend")
- Docker container names (e.g., "myawesomeproject_backend")
- Description
- Author information
"""

import re
import sys
from pathlib import Path


class TemplateCustomizer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.replacements: dict[str, str] = {}

        # Verify we're in a renamed directory (not the original template)
        self.verify_directory_name()

    def verify_directory_name(self) -> None:
        """Verify that we're in a renamed directory, not the original template."""
        current_dir = self.project_root.name

        # If it's still the default template name, this is an error
        if current_dir == "fast-api-template":
            print("❌ Error: You're still in the 'fast-api-template' directory!")
            print("")
            print("This script should be run AFTER renaming the directory.")
            print("")
            print("Please run the rename script first:")
            print("   ./scripts/rename_template.sh")
            print("")
            print("Then restart VS Code and open the renamed directory.")
            sys.exit(1)
        elif not current_dir.endswith("_backend"):
            print("❌ Error: This doesn't appear to be a renamed project directory!")
            print("")
            print(
                "This script should be run from a renamed project directory (ending with _backend)."
            )
            print("")
            print("Please run the rename script first:")
            print("   ./scripts/rename_template.sh")
            print("")
            print("Then restart VS Code and open the renamed directory.")
            sys.exit(1)
        else:
            print(f"✅ Directory name looks good: {current_dir}")
            print("   This appears to be a renamed template directory.")

    def get_user_input(self) -> None:
        """Get project details from user input."""
        print("🚀 FastAPI Template Customization - Step 2")
        print("=" * 50)
        print("This script will transform the template into your custom project.")
        print("Please provide the following information:\n")

        # Project name (human readable)
        project_name = input("Project name (e.g., 'My Awesome Project'): ").strip()
        if not project_name:
            print("❌ Project name is required!")
            sys.exit(1)

        # Project slug (for directories, databases, etc.)
        project_slug = input(
            "Project slug (e.g., 'myawesomeproject_backend'): "
        ).strip()
        if not project_slug:
            # Auto-generate from project name and append _backend
            project_slug = re.sub(r"[^a-zA-Z0-9]", "_", project_name.lower())
            project_slug = re.sub(r"_+", "_", project_slug).strip("_")
            project_slug = f"{project_slug}_backend"
            print(f"   Auto-generated slug: {project_slug}")
        elif not project_slug.endswith("_backend"):
            # Ensure it ends with _backend
            project_slug = f"{project_slug}_backend"
            print(f"   Updated slug to: {project_slug}")

        # Database name
        db_name = input(
            f"Database name (e.g., '{project_slug}', default: {project_slug}): "
        ).strip()
        if not db_name:
            db_name = project_slug

        # Docker project name
        docker_name = input(
            f"Docker project name (e.g., '{project_slug}', default: {project_slug}): "
        ).strip()
        if not docker_name:
            docker_name = project_slug

        # Description
        description = input(
            "Project description (e.g., 'A FastAPI backend for my awesome project'): "
        ).strip()
        if not description:
            description = f"{project_name} with Authentication"

        # Author information
        author = input("Author name (e.g., 'Your Name'): ").strip()
        if not author:
            author = "Your Name"

        email = input("Author email (e.g., 'your.email@example.com'): ").strip()
        if not email:
            email = "your.email@example.com"

        # Confirm customization
        print("\n📋 Customization Summary:")
        print(f"  Project Name: {project_name}")
        print(f"  Project Slug: {project_slug}")
        print(f"  Database Name: {db_name}")
        print(f"  Docker Name: {docker_name}")
        print(f"  Description: {description}")
        print(f"  Author: {author} <{email}>")
        print("")

        confirm = input("Proceed with customization? (y/N): ").strip().lower()
        if confirm not in ["y", "yes"]:
            print("❌ Customization cancelled.")
            sys.exit(0)

        # Store replacements
        self.replacements = {
            "fast-api-template": project_slug,
            "fastapi_template": db_name,
            "FastAPI Template": project_name,
            "FastAPI Template with Authentication": description,
            "Your Name": author,
            "your.email@example.com": email,
            "fast-api-template-postgres-1": f"{docker_name}-postgres-1",
        }
        self.docker_project_name = docker_name

    def get_files_to_process(self) -> list[Path]:
        """Get list of files that need template references replaced."""
        files_to_process = []

        # Define file patterns to process
        patterns = [
            "*.py",
            "*.md",
            "*.yml",
            "*.yaml",
            "*.toml",
            "*.txt",
            "*.sh",
            "*.html",
            "*.css",
            "*.js",
            "*.json",
            "*.ini",
            "*.cfg",
            ".env*",  # Include .env files
        ]

        # Directories to skip
        skip_dirs = {
            ".git",
            "__pycache__",
            "venv",
            "node_modules",
            ".pytest_cache",
            "migrations",
            "alembic/versions",
        }

        # Files to skip (these are handled specially)
        skip_files = {
            "alembic.ini",  # Handled by env.py using settings
        }

        for pattern in patterns:
            for file_path in self.project_root.rglob(pattern):
                # Skip directories in skip list
                if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                    continue

                # Skip specific files
                if file_path.name in skip_files:
                    continue

                # Skip binary files and very large files
                if (
                    file_path.is_file() and file_path.stat().st_size < 1024 * 1024
                ):  # 1MB limit
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            content = f.read()
                            # Check if file contains template references
                            if any(old in content for old in self.replacements.keys()):
                                files_to_process.append(file_path)
                    except (OSError, UnicodeDecodeError):
                        # Skip binary files or files we can't read
                        continue

        return files_to_process

    def process_file(self, file_path: Path) -> bool:
        """Process a single file, replacing template references."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Replace template references
            for old, new in self.replacements.items():
                content = content.replace(old, new)

            # Special handling for README.md
            if file_path.name == "README.md":
                content = self.customize_readme(content)

            # Write back if content changed
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return True

            return False

        except Exception as e:
            print(f"   ⚠️  Warning: Could not process {file_path}: {e}")
            return False

    def customize_readme(self, content: str) -> str:
        """Customize the README.md file for the new project."""
        # Replace the project title
        content = re.sub(
            r"# Your Project Name",
            f"# {self.replacements.get('FastAPI Template', 'Your Project')}",
            content,
        )

        # Update the welcome message
        content = re.sub(
            r"Welcome to your new FastAPI project! 🎉",
            f"Welcome to {self.replacements.get('FastAPI Template', 'your new FastAPI project')}! 🎉",
            content,
        )

        return content

    def update_git_remote(self) -> None:
        """Update git remote information."""
        git_config = self.project_root / ".git" / "config"
        if git_config.exists():
            print("   📝 Note: Remember to update your git remote:")
            print("      git remote set-url origin <your-repo-url>")

    def update_env_file(self) -> None:
        """Update the .env file with the new Docker project name."""
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"

        # Use .env.example if .env doesn't exist
        source_file = env_file if env_file.exists() else env_example

        if source_file.exists():
            try:
                with open(source_file, encoding="utf-8") as f:
                    content = f.read()

                # Update COMPOSE_PROJECT_NAME
                if "COMPOSE_PROJECT_NAME=" in content:
                    content = re.sub(
                        r"COMPOSE_PROJECT_NAME=.*",
                        f"COMPOSE_PROJECT_NAME={self.docker_project_name}",
                        content,
                    )
                else:
                    # Add COMPOSE_PROJECT_NAME if it doesn't exist
                    content += f"\n# Docker Compose project name\nCOMPOSE_PROJECT_NAME={self.docker_project_name}\n"

                # Write to .env file
                with open(env_file, "w", encoding="utf-8") as f:
                    f.write(content)

                print("   ✅ Updated: .env file with Docker project name")

            except Exception as e:
                print(f"   ⚠️  Warning: Could not update .env file: {e}")

    def create_customization_log(self) -> None:
        """Create a log file documenting the customization."""
        log_content = f"""# Template Customization Log

This file documents the customization performed on the FastAPI template.

## Customization Details
- Project Name: {self.replacements.get('FastAPI Template', 'Unknown')}
- Project Slug: {self.replacements.get('fast-api-template', 'Unknown')}
- Database Name: {self.replacements.get('fastapi_template', 'Unknown')}
- Docker Prefix: {self.replacements.get('fast-api-template-postgres-1', 'Unknown').replace('-postgres-1', '')}
- Description: {self.replacements.get('FastAPI Template with Authentication', 'Unknown')}
- Author: {self.replacements.get('Your Name', 'Unknown')} <{self.replacements.get('your.email@example.com', 'Unknown')}>

## What Was Changed
- All template references replaced with project-specific names
- Database configuration updated
- Docker container names updated (using COMPOSE_PROJECT_NAME to prevent conflicts)
- Documentation updated to reflect new project name
- Configuration files updated
- README.md customized for your project (template docs preserved in docs/TEMPLATE_README.md)
- .env file updated with COMPOSE_PROJECT_NAME to ensure unique container names

## Next Steps
1. Review the changes made to ensure they meet your requirements
2. Update the git remote to point to your new repository
3. Run the setup script: ./scripts/setup_project.sh
4. Start developing your application!

## Template Credits
This project was created using the FastAPI Template.
Original template: https://github.com/your-username/fast-api-template
"""

        # Create docs directory if it doesn't exist
        docs_dir = self.project_root / "docs"
        docs_dir.mkdir(exist_ok=True)

        log_file = docs_dir / "TEMPLATE_CUSTOMIZATION.md"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(log_content)

    def run(self) -> None:
        """Run the complete customization process."""
        print("🚀 Starting template customization...\n")

        # Get user input
        self.get_user_input()

        # Get files to process
        print("\n📁 Scanning files for template references...")
        files_to_process = self.get_files_to_process()
        print(f"   Found {len(files_to_process)} files to process\n")

        # Process files
        print("🔄 Processing files...")
        processed_count = 0

        for file_path in files_to_process:
            relative_path = file_path.relative_to(self.project_root)
            if self.process_file(file_path):
                print(f"   ✅ Updated: {relative_path}")
                processed_count += 1

        print("\n📊 Customization Summary:")
        print(f"   Files processed: {len(files_to_process)}")
        print(f"   Files updated: {processed_count}")

        # Update .env file with Docker project name
        self.update_env_file()

        # Create customization log
        self.create_customization_log()
        print("   📝 Created: docs/TEMPLATE_CUSTOMIZATION.md")

        # Update git remote info
        self.update_git_remote()

        print("\n🎉 STEP 2 COMPLETE!")
        print("==================")
        print("\n📋 Next Steps:")
        print("1. Review the changes in docs/TEMPLATE_CUSTOMIZATION.md")
        print("2. Update your git remote: git remote set-url origin <your-repo-url>")
        print("3. Run the setup script: ./scripts/setup_project.sh")
        print("4. Start developing your application!")
        print("\n✨ Happy coding!")


def main():
    """Main entry point."""
    try:
        customizer = TemplateCustomizer()
        customizer.run()
    except KeyboardInterrupt:
        print("\n❌ Customization cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during customization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
