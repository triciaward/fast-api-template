#!/usr/bin/env python3
"""
FastAPI Template Customization Script

This script transforms the FastAPI template into a custom project by replacing
all template-specific references with user-provided project details.

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

        # Check if already customized
        self.check_already_customized()

    def check_already_customized(self) -> None:
        """Check if the template has already been customized."""
        # Check if the directory name is not the default template name
        if self.project_root.name != "fast-api-template":
            print("⚠️  Warning: This appears to be an already customized project!")
            print(f"   Current directory name: {self.project_root.name}")
            print("   Expected template name: fast-api-template")
            print("\n   This script is designed to run on the original template.")
            print("   If you want to customize a new project, please:")
            print("   1. Clone the template again")
            print("   2. Run this script on the fresh template")

            confirm = input("\nContinue anyway? (y/N): ").strip().lower()
            if confirm not in ["y", "yes"]:
                print("❌ Customization cancelled.")
                sys.exit(0)

    def get_user_input(self) -> None:
        """Get project details from user input."""
        print("🚀 FastAPI Template Customization")
        print("=" * 50)
        print(
            "This script will transform the FastAPI template into your custom project."
        )
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
            # Auto-generate from project name
            project_slug = re.sub(r"[^a-zA-Z0-9]", "_", project_name.lower())
            project_slug = re.sub(r"_+", "_", project_slug).strip("_")
            print(f"   Auto-generated slug: {project_slug}")

        # Database name
        db_name = input(
            f"Database name (e.g., '{project_slug}', default: {project_slug}): "
        ).strip()
        if not db_name:
            db_name = project_slug

        # Docker container prefix
        docker_prefix = input(
            f"Docker container prefix (e.g., '{project_slug}', default: {project_slug}): "
        ).strip()
        if not docker_prefix:
            docker_prefix = project_slug

        # Description
        description = input(
            "Project description (default: 'FastAPI application'): "
        ).strip()
        if not description:
            description = "FastAPI application"

        # Author
        author = input("Author name (default: 'Your Name'): ").strip()
        if not author:
            author = "Your Name"

        # Email
        email = input("Author email (default: 'your.email@example.com'): ").strip()
        if not email:
            email = "your.email@example.com"

        # Confirm
        print("\n" + "=" * 50)
        print("📋 Summary:")
        print(f"   Project Name: {project_name}")
        print(f"   Project Slug: {project_slug}")
        print(f"   Database Name: {db_name}")
        print(f"   Docker Prefix: {docker_prefix}")
        print(f"   Description: {description}")
        print(f"   Author: {author} <{email}>")
        print("=" * 50)

        confirm = input("\nProceed with customization? (y/N): ").strip().lower()
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
            "fast-api-template-postgres-1": f"{docker_prefix}-postgres-1",
            "fast-api-template-postgres": f"{docker_prefix}-postgres",
        }

        # Store Docker project name for environment file
        self.docker_project_name = docker_prefix

    def get_files_to_process(self) -> list[Path]:
        """Get list of files that need template customization."""
        files_to_process = []

        # File patterns to process
        patterns = [
            "*.py",
            "*.md",
            "*.yml",
            "*.yaml",
            "*.toml",
            "*.ini",
            "*.sh",
            "*.txt",
            "*.cfg",
            "*.conf",
            "*.env*",
            "Dockerfile",
        ]

        # Directories to skip
        skip_dirs = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            "venv",
            "node_modules",
            "alembic/versions",  # Skip migration files
        }

        for pattern in patterns:
            for file_path in self.project_root.rglob(pattern):
                # Skip directories in skip list
                if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                    continue

                # Skip binary files and very large files
                if (
                    file_path.is_file() and file_path.stat().st_size < 1024 * 1024
                ):  # 1MB limit
                    try:
                        # Try to read as text to ensure it's a text file
                        with open(file_path, encoding="utf-8") as f:
                            f.read()
                        files_to_process.append(file_path)
                    except (UnicodeDecodeError, PermissionError):
                        # Skip binary files or files we can't read
                        continue

        return files_to_process

    def process_file(self, file_path: Path) -> bool:
        """Process a single file and replace template references."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Special handling for README.md
            if file_path.name == "README.md":
                content = self.customize_readme(content)

            # Apply replacements (but preserve template documentation links)
            for old_text, new_text in self.replacements.items():
                # Skip replacing "FastAPI Template" in template documentation links
                if old_text == "FastAPI Template":
                    # Replace all instances except those in template doc links
                    import re

                    content = re.sub(
                        r"FastAPI Template(?!.*docs/TEMPLATE_README\.md)",
                        new_text,
                        content,
                    )
                else:
                    content = content.replace(old_text, new_text)

            # If content changed, write it back
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return True

        except Exception as e:
            print(f"   ⚠️  Warning: Could not process {file_path}: {e}")

        return False

    def customize_readme(self, content: str) -> str:
        """Customize the README.md content for the user's project."""
        project_name = self.replacements.get("FastAPI Template", "Your Project Name")

        # Replace the title
        content = content.replace("# Your Project Name", f"# {project_name}")

        # Keep the template link unchanged - we want to preserve the link to template docs
        # The general replacements will handle other instances of "FastAPI Template"

        return content

    def rename_project_directory(self) -> None:
        """Provide instructions for renaming the project directory and create VS Code workspace."""
        current_dir = self.project_root.name
        new_name = self.replacements.get("fast-api-template", current_dir)

        if current_dir != new_name:
            print("   📁 Directory Renaming Instructions:")
            print(f"   Current directory: {current_dir}")
            print(f"   Recommended name: {new_name}")

            # Note: VS Code workspace file creation removed to prevent workspace conflicts

            print("\n   🔧 To rename the directory and update VS Code:")
            print("   1. Close VS Code completely")
            print("   2. Open Terminal/Command Prompt")
            print("   3. Navigate to the parent directory:")
            print(f"      cd {self.project_root.parent}")
            print("   4. Rename the directory:")
            print(f"      mv {current_dir} {new_name}")
            print("   5. Open the renamed directory in VS Code:")
            print(f"      code {new_name}")
            print("      # OR: File → Open Folder → select the renamed directory")
            print("   6. After renaming, open the new directory in VS Code")

            print(
                "\n   📝 Note: VS Code workspace file creation disabled to prevent conflicts"
            )

        else:
            print(f"   ✅ Directory name is already correct: {current_dir}")

    def create_vscode_workspace(self, project_path: Path, project_name: str) -> None:
        """Create a VS Code workspace file to help with the transition."""
        vscode_dir = project_path / ".vscode"
        vscode_dir.mkdir(exist_ok=True)

        workspace_content = f"""{{
    "folders": [
        {{
            "name": "{project_name}",
            "path": "."
        }}
    ],
    "settings": {{
        "python.defaultInterpreterPath": "./venv/bin/python",
        "python.terminal.activateEnvironment": true,
        "files.exclude": {{
            "**/__pycache__": true,
            "**/*.pyc": true,
            "**/.pytest_cache": true,
            "**/.mypy_cache": true,
            "**/.ruff_cache": true,
            "**/venv": true
        }}
    }},
    "extensions": {{
        "recommendations": [
            "ms-python.python",
            "ms-python.black-formatter",
            "ms-python.flake8",
            "ms-python.mypy-type-checker",
            "charliermarsh.ruff"
        ]
    }}
}}"""

        workspace_file = vscode_dir / "project.code-workspace"
        with open(workspace_file, "w", encoding="utf-8") as f:
            f.write(workspace_content)

        print("   📝 Created VS Code workspace: .vscode/project.code-workspace")

    def update_git_remote(self) -> None:
        """Update git remote if it points to the template repository."""
        try:
            import subprocess

            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode == 0:
                remote_url = result.stdout.strip()
                if "fast-api-template" in remote_url.lower():
                    print("\n🔗 Git Remote Update")
                    print(
                        "   The current git remote points to the template repository."
                    )
                    print("   You should update it to point to your new repository:")
                    print("   git remote set-url origin <your-new-repo-url>")
                    print(
                        "   git remote add upstream <template-repo-url>  # Optional: keep template as upstream"
                    )

        except Exception:
            # Git not available or not a git repo
            pass

    def update_env_file(self) -> None:
        """Update or create .env file with project-specific Docker settings."""
        env_file = self.project_root / ".env"

        # Read existing .env file if it exists
        env_content = ""
        if env_file.exists():
            with open(env_file, encoding="utf-8") as f:
                env_content = f.read()

        # Add or update COMPOSE_PROJECT_NAME
        if "COMPOSE_PROJECT_NAME=" in env_content:
            # Update existing line
            import re

            env_content = re.sub(
                r"COMPOSE_PROJECT_NAME=.*",
                f"COMPOSE_PROJECT_NAME={self.docker_project_name}",
                env_content,
            )
        else:
            # Add new line
            env_content += f"\n# Docker Compose project name (prevents container naming conflicts)\nCOMPOSE_PROJECT_NAME={self.docker_project_name}\n"

        # Write back to file
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)

        print(
            f"   ✅ Updated: .env (added COMPOSE_PROJECT_NAME={self.docker_project_name})"
        )

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
3. Run the setup script: ./scripts/setup_comprehensive.sh
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
        print("📁 Scanning files for template references...")
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

        # Provide renaming instructions
        print("\n📁 Directory Renaming Instructions...")
        self.rename_project_directory()

        # Update git remote info
        self.update_git_remote()

        print("\n🎉 Template customization completed successfully!")
        print("\n📋 Next Steps:")
        print("   1. Review the changes in docs/TEMPLATE_CUSTOMIZATION.md")
        print("   2. Follow the directory renaming instructions above")
        print("   3. Update your git remote: git remote set-url origin <your-repo-url>")
        print("   4. Run setup: ./scripts/setup_comprehensive.sh")
        print("   5. Start developing your application!")
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
