#!/usr/bin/env python3
"""
Demonstration script for standardized error responses.

This script shows how the standardized error response system works
by making various API calls that trigger different types of errors.
"""

import json
import sys

import requests

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


def print_error_response(title: str, response: requests.Response) -> None:
    """Print a formatted error response."""

    try:
        data = response.json()

        # Check if it's a standardized error response
        if "error" in data:
            error = data["error"]
            if error.get("details"):
                pass
        else:
            pass

    except json.JSONDecodeError:
        pass


def demo_validation_errors() -> None:
    """Demonstrate validation errors."""

    # Invalid email format
    response = requests.post(
        f"{API_BASE}/auth/register",
        json={
            "email": "invalid-email",
            "username": "testuser",
            "password": "TestPassword123!",
        },
    )
    print_error_response("Invalid Email Format", response)

    # Missing required fields
    response = requests.post(
        f"{API_BASE}/auth/register",
        json={
            "email": "test@example.com",
            # Missing username and password
        },
    )
    print_error_response("Missing Required Fields", response)


def demo_authentication_errors() -> None:
    """Demonstrate authentication errors."""

    # Invalid credentials
    response = requests.post(
        f"{API_BASE}/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword",
        },
    )
    print_error_response("Invalid Credentials", response)

    # No authentication token
    response = requests.get(f"{API_BASE}/admin/users")
    print_error_response("No Authentication Token", response)


def demo_conflict_errors() -> None:
    """Demonstrate conflict errors."""

    # Create first user
    response = requests.post(
        f"{API_BASE}/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "TestPassword123!",
        },
    )
    if response.status_code == 201:
        pass
    else:
        print_error_response("First User Creation Failed", response)
        return

    # Try to create second user with same email
    response = requests.post(
        f"{API_BASE}/auth/register",
        json={
            "email": "duplicate@example.com",  # Same email
            "username": "user2",
            "password": "TestPassword456!",
        },
    )
    print_error_response("Duplicate Email Conflict", response)


def demo_not_found_errors() -> None:
    """Demonstrate not found errors."""

    # Non-existent endpoint (this will use FastAPI's default 404)
    response = requests.get(f"{API_BASE}/nonexistent-endpoint")
    print_error_response("Non-existent Endpoint", response)


def demo_rate_limit_errors() -> None:
    """Demonstrate rate limit errors."""


    # For demonstration, we'll show what the error format would look like


def demo_server_errors() -> None:
    """Demonstrate server errors."""


    # For demonstration, we'll show what the error format would look like


def demo_custom_exceptions() -> None:
    """Demonstrate custom exception usage."""



def main() -> None:
    """Run the error response demonstration."""

    try:
        # Test server connectivity
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            sys.exit(1)

        # Run demonstrations
        demo_validation_errors()
        demo_authentication_errors()
        demo_conflict_errors()
        demo_not_found_errors()
        demo_rate_limit_errors()
        demo_server_errors()
        demo_custom_exceptions()


    except requests.exceptions.ConnectionError:
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
