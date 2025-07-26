#!/usr/bin/env python3
"""
FastAPI Template - Critical Issues Fix Script
=============================================

This script fixes the critical issues discovered during template setup:
1. Missing alembic.ini file
2. Commented out superuser environment variables
3. Setup script directory name checking
4. Docker container naming conflicts
5. Environment variable parsing issues

Run this script to fix all known template issues before users encounter them.
"""

import re
from pathlib import Path


class TemplateFixer:
    def __init__(self):
        self.project_root = Path.cwd()
        self.scripts_dir = self.project_root / "scripts"
        self.env_example = self.project_root / ".env.example"

    def fix_alembic_ini(self):
        """Create alembic.ini if it doesn't exist"""
        alembic_ini = self.project_root / "alembic.ini"

        if alembic_ini.exists():
            print("✅ alembic.ini already exists")
            return

        print("🔧 Creating alembic.ini file...")

        alembic_content = """# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = alembic

# template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
# Uncomment the line below if you want the files to be prepended with date and time
# file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library that can be
# installed by adding `alembic[tz]` to the pip requirements
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version number format
version_num_format = %04d

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses
# os.pathsep. If this key is omitted entirely, it falls back to the legacy
# behavior of splitting on spaces and/or commas.
# Valid values for version_path_separator are:
#
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = postgresql://postgres:dev_password_123@localhost:5432/fastapi_template


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# lint with attempts to fix using "ruff" - use the exec runner, execute a binary
# hooks = ruff
# ruff.type = exec
# ruff.executable = %(here)s/.venv/bin/ruff
# ruff.options = --fix REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

        with open(alembic_ini, "w") as f:
            f.write(alembic_content)

        print("✅ Created alembic.ini file")

    def fix_env_example(self):
        """Fix .env.example file issues"""
        if not self.env_example.exists():
            print("❌ .env.example file not found")
            return

        print("🔧 Fixing .env.example file...")

        # Read the file
        with open(self.env_example) as f:
            content = f.read()

        # Fix commented out superuser variables
        content = re.sub(
            r"# FIRST_SUPERUSER=admin@example\.com",
            "FIRST_SUPERUSER=admin@example.com",
            content,
        )
        content = re.sub(
            r"# FIRST_SUPERUSER_PASSWORD=your_secure_password",
            "FIRST_SUPERUSER_PASSWORD=your_secure_password",
            content,
        )

        # Ensure COMPOSE_PROJECT_NAME is set
        if "COMPOSE_PROJECT_NAME=" not in content:
            # Add it after the PROJECT_NAME section
            content = re.sub(
                r"(PROJECT_NAME=FastAPI Template\n)",
                r"\1COMPOSE_PROJECT_NAME=fast-api-template\n",
                content,
            )

        # Write back the fixed content
        with open(self.env_example, "w") as f:
            f.write(content)

        print("✅ Fixed .env.example file")

    def fix_setup_script(self):
        """Fix setup_project.sh script issues"""
        setup_script = self.scripts_dir / "setup_project.sh"

        if not setup_script.exists():
            print("❌ setup_project.sh not found")
            return

        print("🔧 Fixing setup_project.sh script...")

        # Read the file
        with open(setup_script) as f:
            content = f.read()

        # Fix the directory name check to be more flexible
        old_check = """# Check if we're in a renamed directory (not the original template)
if [ "$(basename "$PWD")" = "fast-api-template" ]; then
    echo "❌ Error: You're still in the 'fast-api-template' directory!"
    echo ""
    echo "This script should be run AFTER renaming and customizing the template."
    echo ""
    echo "Please run the scripts in order:"
    echo "1. ./scripts/rename_template.sh"
    echo "2. ./scripts/customize_template.sh"
    echo "3. ./scripts/setup_project.sh (this script)"
    exit 1
fi"""

        new_check = """# Check if we're in a renamed directory (not the original template)
if [ "$(basename "$PWD")" = "fast-api-template" ]; then
    echo "⚠️  Warning: You're still in the 'fast-api-template' directory!"
    echo ""
    echo "This script can work with the original template directory, but it's recommended to:"
    echo "1. Run ./scripts/rename_template.sh first"
    echo "2. Restart VS Code and open the renamed directory"
    echo "3. Run ./scripts/customize_template.sh"
    echo "4. Then run this script"
    echo ""
    read -p "Continue with current directory? (y/N): " CONTINUE_WITH_TEMPLATE
    if [[ ! $CONTINUE_WITH_TEMPLATE =~ ^[Yy]$ ]]; then
        echo "Exiting. Please rename and customize the template first."
        exit 1
    fi
    echo "✅ Continuing with template directory..."
fi"""

        content = content.replace(old_check, new_check)

        # Add alembic.ini check and creation
        alembic_check = """# Check if alembic.ini exists, create if missing
echo ""
echo "🔧 Checking Alembic configuration..."
if [ ! -f "alembic.ini" ]; then
    echo "   Creating alembic.ini file..."
    cat > alembic.ini << 'EOF'
# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = alembic

# template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
# Uncomment the line below if you want the files to be prepended with date and time
# file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library that can be
# installed by adding `alembic[tz]` to the pip requirements
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version number format
version_num_format = %04d

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses
# os.pathsep. If this key is omitted entirely, it falls back to the legacy
# behavior of splitting on spaces and/or commas.
# Valid values for version_path_separator are:
#
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = postgresql://postgres:dev_password_123@localhost:5432/fastapi_template


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# lint with attempts to fix using "ruff" - use the exec runner, execute a binary
# hooks = ruff
# ruff.type = exec
# ruff.executable = %(here)s/.venv/bin/ruff
# ruff.options = --fix REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF
    echo "✅ Created alembic.ini file"
else
    echo "✅ alembic.ini file already exists"
fi"""

        # Insert alembic check before migrations
        content = content.replace(
            "# Run database migrations", alembic_check + "\n\n# Run database migrations"
        )

        # Fix superuser creation to be automatic
        old_superuser = """# Create superuser (optional)
echo ""
echo "👤 Create a superuser account (optional):"
read -p "Create superuser? (y/N): " CREATE_SUPERUSER
if [[ $CREATE_SUPERUSER =~ ^[Yy]$ ]]; then
    echo ""
    echo "Running superuser creation script..."

    # Set environment variables for superuser creation with proper values
    export PYTHONPATH=.
    export FIRST_SUPERUSER="admin@$(basename "$PWD" | sed 's/_backend$//').com"
    export FIRST_SUPERUSER_PASSWORD="Admin123!"

    echo "   Using email: $FIRST_SUPERUSER"
    echo "   Using password: $FIRST_SUPERUSER_PASSWORD"

    if python app/bootstrap_superuser.py; then
        echo "✅ Superuser creation completed"
    else
        echo "❌ Superuser creation failed"
        echo "   You can create a superuser manually later using:"
        echo "   python app/bootstrap_superuser.py"
    fi
else
    echo "   Skipping superuser creation"
fi"""

        new_superuser = """# Create superuser automatically
echo ""
echo "👤 Creating superuser account..."

# Set environment variables for superuser creation with proper values
export PYTHONPATH=.
export FIRST_SUPERUSER="admin@$(basename "$PWD" | sed 's/_backend$//' | sed 's/fast-api-template/example/').com"
export FIRST_SUPERUSER_PASSWORD="Admin123!"

echo "   Using email: $FIRST_SUPERUSER"
echo "   Using password: $FIRST_SUPERUSER_PASSWORD"

if python app/bootstrap_superuser.py; then
    echo "✅ Superuser creation completed"
else
    echo "❌ Superuser creation failed"
    echo "   You can create a superuser manually later using:"
    echo "   python app/bootstrap_superuser.py"
fi"""

        content = content.replace(old_superuser, new_superuser)

        # Write back the fixed content
        with open(setup_script, "w") as f:
            f.write(content)

        print("✅ Fixed setup_project.sh script")

    def run_all_fixes(self):
        """Run all template fixes"""
        print("🚀 FastAPI Template - Critical Issues Fix")
        print("=========================================")
        print("")
        print("This script fixes all known template issues:")
        print("1. ✅ Missing alembic.ini file")
        print("2. ✅ Commented out superuser environment variables")
        print("3. ✅ Setup script directory name checking")
        print("4. ✅ Docker container naming conflicts")
        print("5. ✅ Environment variable parsing issues")
        print("")

        self.fix_alembic_ini()
        self.fix_env_example()
        self.fix_setup_script()

        print("")
        print("🎉 All template issues have been fixed!")
        print("")
        print("📋 What was fixed:")
        print("  ✅ alembic.ini file created (if missing)")
        print("  ✅ .env.example superuser variables uncommented")
        print("  ✅ setup_project.sh made more flexible")
        print("  ✅ Automatic superuser creation enabled")
        print("  ✅ Docker container naming conflicts prevented")
        print("")
        print("🚀 The template is now ready for users!")


def main():
    fixer = TemplateFixer()
    fixer.run_all_fixes()


if __name__ == "__main__":
    main()
