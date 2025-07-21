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
    print(f"\n{'='*60}")
    print(f"🔴 {title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"URL: {response.url}")

    try:
        data = response.json()
        print("\n📋 Response Body:")
        print(json.dumps(data, indent=2))

        # Check if it's a standardized error response
        if "error" in data:
            error = data["error"]
            print("\n✅ Standardized Error Response:")
            print(f"   Type: {error.get('type', 'N/A')}")
            print(f"   Message: {error.get('message', 'N/A')}")
            print(f"   Code: {error.get('code', 'N/A')}")
            if error.get("details"):
                print(f"   Details: {error.get('details')}")
        else:
            print("\n⚠️  Non-standardized Error Response:")
            print(f"   Detail: {data.get('detail', 'N/A')}")

    except json.JSONDecodeError:
        print("\n❌ Invalid JSON response:")
        print(response.text)


def demo_validation_errors() -> None:
    """Demonstrate validation errors."""
    print("\n🚨 VALIDATION ERROR DEMOS")
    print("=" * 40)

    # Invalid email format
    print("\n1. Invalid Email Format")
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
    print("\n2. Missing Required Fields")
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
    print("\n🔐 AUTHENTICATION ERROR DEMOS")
    print("=" * 40)

    # Invalid credentials
    print("\n1. Invalid Credentials")
    response = requests.post(
        f"{API_BASE}/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword",
        },
    )
    print_error_response("Invalid Credentials", response)

    # No authentication token
    print("\n2. No Authentication Token")
    response = requests.get(f"{API_BASE}/admin/users")
    print_error_response("No Authentication Token", response)


def demo_conflict_errors() -> None:
    """Demonstrate conflict errors."""
    print("\n⚡ CONFLICT ERROR DEMOS")
    print("=" * 40)

    # Create first user
    print("\n1. Creating First User")
    response = requests.post(
        f"{API_BASE}/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "TestPassword123!",
        },
    )
    if response.status_code == 201:
        print("✅ First user created successfully")
    else:
        print_error_response("First User Creation Failed", response)
        return

    # Try to create second user with same email
    print("\n2. Duplicate Email Conflict")
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
    print("\n🔍 NOT FOUND ERROR DEMOS")
    print("=" * 40)

    # Non-existent endpoint (this will use FastAPI's default 404)
    print("\n1. Non-existent Endpoint")
    response = requests.get(f"{API_BASE}/nonexistent-endpoint")
    print_error_response("Non-existent Endpoint", response)


def demo_rate_limit_errors() -> None:
    """Demonstrate rate limit errors."""
    print("\n⏱️  RATE LIMIT ERROR DEMOS")
    print("=" * 40)

    print("\n1. Rate Limit Exceeded (simulated)")
    print("Note: This would require hitting actual rate limits.")
    print("In a real scenario, making many rapid requests would trigger this.")

    # For demonstration, we'll show what the error format would look like
    demo_rate_limit_response = {
        "error": {
            "type": "RateLimitExceeded",
            "message": "Too many requests. Please try again later.",
            "code": "rate_limit_exceeded",
            "retry_after": 60,
            "limit": 100,
        }
    }
    print("\n📋 Example Rate Limit Error Response:")
    print(json.dumps(demo_rate_limit_response, indent=2))


def demo_server_errors() -> None:
    """Demonstrate server errors."""
    print("\n💥 SERVER ERROR DEMOS")
    print("=" * 40)

    print("\n1. Server Error (simulated)")
    print("Note: This would require triggering an actual server error.")
    print(
        "In a real scenario, database failures or other server issues would trigger this."
    )

    # For demonstration, we'll show what the error format would look like
    demo_server_response = {
        "error": {
            "type": "InternalServerError",
            "message": "An unexpected error occurred",
            "code": "internal_error",
            "request_id": "req_123456",
            "details": {"exception_type": "DatabaseError"},
        }
    }
    print("\n📋 Example Server Error Response:")
    print(json.dumps(demo_server_response, indent=2))


def demo_custom_exceptions() -> None:
    """Demonstrate custom exception usage."""
    print("\n🛠️  CUSTOM EXCEPTION USAGE")
    print("=" * 40)

    print("\n1. Using Custom Exceptions in Code")
    print(
        """
# Example usage in your FastAPI endpoints:

from app.core.exceptions import (
    raise_validation_error,
    raise_authentication_error,
    raise_not_found_error,
    raise_conflict_error
)

# Validation error
raise_validation_error(
    message="Email format is invalid",
    code=ErrorCode.INVALID_EMAIL,
    field="email",
    value="invalid-email"
)

# Authentication error
raise_authentication_error(
    message="Invalid credentials",
    code=ErrorCode.INVALID_CREDENTIALS
)

# Not found error
raise_not_found_error(
    message="User not found",
    code=ErrorCode.USER_NOT_FOUND,
    resource_type="user",
    resource_id="123"
)

# Conflict error
raise_conflict_error(
    message="Email already exists",
    code=ErrorCode.EMAIL_ALREADY_EXISTS,
    conflicting_field="email",
    conflicting_value="user@example.com"
)
    """
    )


def main() -> None:
    """Run the error response demonstration."""
    print("🚨 STANDARDIZED ERROR RESPONSES DEMONSTRATION")
    print("=" * 60)
    print("This script demonstrates the standardized error response system.")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("=" * 60)

    try:
        # Test server connectivity
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print(f"❌ Server not responding properly. Status: {response.status_code}")
            sys.exit(1)
        print("✅ Server is running and responding")

        # Run demonstrations
        demo_validation_errors()
        demo_authentication_errors()
        demo_conflict_errors()
        demo_not_found_errors()
        demo_rate_limit_errors()
        demo_server_errors()
        demo_custom_exceptions()

        print("\n" + "=" * 60)
        print("🎉 DEMONSTRATION COMPLETE")
        print("=" * 60)
        print("\nKey Benefits of Standardized Error Responses:")
        print("✅ Consistent error format across all endpoints")
        print("✅ Machine-readable error codes for frontend handling")
        print("✅ Rich error details for debugging")
        print("✅ Request tracking with request IDs")
        print("✅ Comprehensive error categorization")
        print("✅ Easy to extend with new error types")

    except requests.exceptions.ConnectionError:
        print(
            "❌ Could not connect to server. Make sure it's running on http://localhost:8000"
        )
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Demonstration interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
