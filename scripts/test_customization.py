#!/usr/bin/env python3
"""
Test script for the customization process.
This script tests the customization logic without actually renaming directories.
"""

import shutil
import sys
import tempfile
from pathlib import Path


def test_customization_logic():
    """Test the customization script logic without actual file operations."""
    print("🧪 Testing Customization Script Logic")
    print("=" * 50)

    # Test 1: Check if we're in the right directory
    project_root = Path(__file__).parent.parent
    print(f"✅ Project root: {project_root}")
    print(f"✅ Directory name: {project_root.name}")

    # Test 2: Check if customization script exists
    customize_script = project_root / "scripts" / "customize_template.py"
    if customize_script.exists():
        print(f"✅ Customization script found: {customize_script}")
    else:
        print(f"❌ Customization script not found: {customize_script}")
        return False

    # Test 3: Check if shell wrapper exists
    shell_wrapper = project_root / "scripts" / "customize_template.sh"
    if shell_wrapper.exists():
        print(f"✅ Shell wrapper found: {shell_wrapper}")
    else:
        print(f"❌ Shell wrapper not found: {shell_wrapper}")
        return False

    # Test 4: Test the safety check logic
    print("\n🔍 Testing Safety Checks:")
    if project_root.name == "fast-api-template":
        print("✅ Directory name is correct (fast-api-template)")
        print("✅ Script should run normally")
    else:
        print(f"⚠️  Directory name is: {project_root.name}")
        print("⚠️  Script should show warning about already customized project")

    # Test 5: Check for VS Code workspace creation logic
    print("\n🔍 Testing VS Code Workspace Logic:")
    vscode_dir = project_root / ".vscode"
    if vscode_dir.exists():
        print(f"✅ .vscode directory exists: {vscode_dir}")
        workspace_file = vscode_dir / "project.code-workspace"
        if workspace_file.exists():
            print(f"✅ Workspace file exists: {workspace_file}")
        else:
            print("ℹ️  Workspace file will be created during customization")
    else:
        print("ℹ️  .vscode directory will be created during customization")

    print("\n✅ All tests passed!")
    return True


def test_directory_rename_simulation():
    """Simulate the directory rename process in a temporary location."""
    print("\n🧪 Testing Directory Rename Simulation")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a test directory structure
        test_project = temp_path / "fast-api-template"
        test_project.mkdir()

        # Create some test files
        (test_project / "README.md").write_text("# FastAPI Template")
        (test_project / "scripts" / "customize_template.py").parent.mkdir(parents=True)
        (test_project / "scripts" / "customize_template.py").write_text("# Test script")

        print(f"✅ Created test project: {test_project}")

        # Simulate rename
        new_name = "myproject_backend"
        new_path = test_project.parent / new_name

        if new_path.exists():
            print(f"❌ Target directory already exists: {new_path}")
            return False

        # Perform rename
        try:
            shutil.move(str(test_project), str(new_path))
            print(f"✅ Successfully renamed: {test_project.name} → {new_name}")
            print(f"✅ New path: {new_path}")

            # Verify files are intact
            if (new_path / "README.md").exists():
                print("✅ Files preserved after rename")
            else:
                print("❌ Files lost during rename")
                return False

        except Exception as e:
            print(f"❌ Error during rename: {e}")
            return False

    print("✅ Directory rename simulation successful!")
    return True


def main():
    """Run all tests."""
    print("🚀 FastAPI Template Customization Test Suite")
    print("=" * 60)

    success = True

    # Test 1: Basic logic
    if not test_customization_logic():
        success = False

    # Test 2: Directory rename simulation
    if not test_directory_rename_simulation():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! The customization script should work correctly.")
        print("\n📋 To test the actual customization:")
        print("1. Clone the template to a new directory")
        print("2. Run: ./scripts/customize_template.sh")
        print("3. Follow the prompts")
    else:
        print("❌ Some tests failed. Please check the customization script.")
        sys.exit(1)


if __name__ == "__main__":
    main()
