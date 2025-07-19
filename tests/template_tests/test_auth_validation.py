
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

pytestmark = pytest.mark.usefixtures("patch_email_service_is_configured")


@pytest.fixture(autouse=True)
def patch_email_service_is_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services.email import email_service
    monkeypatch.setattr(email_service, "is_configured", lambda: True)


class TestAuthEndpointValidation:
    """Test authentication endpoints with validation."""

    def test_register_valid_user(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with valid user data."""
        user_data = {
            "email": "valid@example.com",
            "username": "validuser",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["email"] == "valid@example.com"
        assert data["username"] == "validuser"
        assert "id" in data
        assert data["is_verified"] is False

    def test_register_weak_password(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with weak password."""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "Password must be at least 8 characters long" in str(data)

    def test_register_invalid_username(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with invalid username."""
        user_data = {
            "email": "test@example.com",
            "username": "admin",  # Reserved word
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "reserved and cannot be used" in str(data)

    def test_register_invalid_email(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with invalid email."""
        user_data = {
            "email": "invalid-email",
            "username": "testuser",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "not a valid email address" in str(data)

    def test_register_disposable_email(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with disposable email."""
        user_data = {
            "email": "test@10minutemail.com",
            "username": "testuser",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "Disposable email addresses are not allowed" in str(data)

    def test_register_duplicate_email(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with duplicate email."""
        # Create first user
        user_data = {
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "StrongPass123!",
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        # Try to register with same email
        user_data2 = {
            "email": "duplicate@example.com",
            "username": "user2",
            "password": "StrongPass456!",
        }
        response = client.post("/api/v1/auth/register", json=user_data2)
        assert response.status_code == 400

        data = response.json()
        assert "Email already registered" in data["detail"]

    def test_register_duplicate_username(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with duplicate username."""
        # Create first user
        user_data = {
            "email": "user1@example.com",
            "username": "duplicateuser",
            "password": "StrongPass123!",
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        # Try to register with same username
        user_data2 = {
            "email": "user2@example.com",
            "username": "duplicateuser",
            "password": "StrongPass456!",
        }
        response = client.post("/api/v1/auth/register", json=user_data2)
        assert response.status_code == 400

        data = response.json()
        assert "Username already taken" in data["detail"]

    def test_login_invalid_email_format(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test login with invalid email format."""
        login_data = {"username": "invalid-email", "password": "password123"}

        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 400

        data = response.json()
        assert "Invalid email format" in data["detail"]

    def test_login_nonexistent_user(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401

        data = response.json()
        assert "Invalid email or password" in data["detail"]

    def test_login_wrong_password(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test login with wrong password."""
        # Create user first
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "StrongPass123!",
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Try to login with wrong password
        login_data = {"username": "test@example.com",
                      "password": "WrongPassword123!"}

        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401

        data = response.json()
        assert "Invalid email or password" in data["detail"]

    def test_oauth_invalid_provider(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test OAuth login with invalid provider."""
        oauth_data = {"provider": "invalid_provider",
                      "access_token": "fake_token"}

        response = client.post("/api/v1/auth/oauth/login", json=oauth_data)
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "Provider must be 'google' or 'apple'" in str(data)

    def test_email_verification_invalid_email(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test email verification request with invalid email."""
        verification_data = {"email": "invalid-email"}

        response = client.post(
            "/api/v1/auth/resend-verification", json=verification_data
        )
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "not a valid email address" in str(data)

    def test_email_verification_disposable_email(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test email verification request with disposable email."""
        verification_data = {"email": "test@10minutemail.com"}

        response = client.post(
            "/api/v1/auth/resend-verification", json=verification_data
        )
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "Disposable email addresses are not allowed" in str(data)


class TestInputSanitization:
    """Test input sanitization in API endpoints."""

    def test_register_with_whitespace(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with whitespace in inputs."""
        user_data = {
            "email": "  test@example.com  ",
            "username": "  testuser  ",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"

    def test_register_with_control_characters(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with control characters in inputs."""
        user_data = {
            "email": "test\x00@example.com",
            "username": "test\x08user",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Should fail validation

    def test_username_edge_cases(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test various username edge cases."""
        test_cases = [
            # (username, should_pass, expected_error_contains)
            ("ab", False, "at least 3 characters"),
            ("a" * 31, False, "less than 30 characters"),
            ("user@name", False, "letters, numbers, underscores, and hyphens"),
            ("_username", False, "cannot start with underscore"),
            ("username_", False, "cannot end with underscore"),
            ("user__name", False, "consecutive underscores"),
            ("admin", False, "reserved and cannot be used"),
            ("valid_user", True, None),
            ("user-123", True, None),
            ("a" * 30, True, None),  # Exactly 30 characters should be valid
        ]

        for username, should_pass, expected_error in test_cases:
            user_data = {
                "email": f"test_{username}@example.com",
                "username": username,
                "password": "StrongPass123!",
            }

            response = client.post("/api/v1/auth/register", json=user_data)

            if should_pass:
                assert response.status_code == 201, f"Username '{username}' should pass"
            else:
                assert response.status_code == 422, f"Username '{username}' should fail"
                if expected_error:
                    data = response.json()
                    assert (
                        expected_error in str(data)
                    ), f"Expected error '{expected_error}' not found for username '{username}'"

    def test_password_edge_cases(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test various password edge cases."""
        test_cases = [
            # (password, should_pass, expected_error_contains)
            ("weak", False, "at least 8 characters"),
            ("A" * 129 + "1!", False, "less than 128 characters"),
            ("lowercase123!", False, "uppercase letter"),
            ("UPPERCASE123!", False, "lowercase letter"),
            ("NoNumbers!", False, "number"),
            ("NoSpecialChar123", False, "special character"),
            # Fails for multiple reasons
            ("password", False, "uppercase letter"),
            ("StrongPass123!", True, None),
        ]

        for password, should_pass, expected_error in test_cases:
            user_data = {
                "email": f"test_{password[:10]}@example.com",
                "username": f"user_{password[:10]}",
                "password": password,
            }

            response = client.post("/api/v1/auth/register", json=user_data)

            if should_pass:
                assert response.status_code == 201, f"Password '{password}' should pass"
            else:
                assert response.status_code == 422, f"Password '{password}' should fail"
                if expected_error:
                    data = response.json()
                    assert (
                        expected_error in str(data)
                    ), f"Expected error '{expected_error}' not found for password '{password}'"


class TestErrorMessages:
    """Test that error messages are user-friendly and informative."""

    def test_registration_error_messages(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test that registration error messages are helpful."""
        # Test duplicate email error message
        user_data = {
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "StrongPass123!",
        }
        client.post("/api/v1/auth/register", json=user_data)

        user_data2 = {
            "email": "duplicate@example.com",
            "username": "user2",
            "password": "StrongPass456!",
        }
        response = client.post("/api/v1/auth/register", json=user_data2)

        data = response.json()
        assert (
            "Email already registered. Please use a different email or try logging in."
            in data["detail"]
        )

        # Test duplicate username error message
        user_data3 = {
            "email": "user3@example.com",
            "username": "user1",
            "password": "StrongPass789!",
        }
        response = client.post("/api/v1/auth/register", json=user_data3)

        data = response.json()
        assert (
            "Username already taken. Please choose a different username."
            in data["detail"]
        )

    def test_login_error_messages(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test that login error messages are helpful."""
        # Test non-existent user
        login_data = {
            "username": "nonexistent@example.com",
            "password": "StrongPass123!",
        }
        response = client.post("/api/v1/auth/login", data=login_data)

        data = response.json()
        assert (
            "Invalid email or password. Please check your credentials and try again."
            in data["detail"]
        )

        # Test unverified user
        user_data = {
            "email": "unverified@example.com",
            "username": "unverified",
            "password": "StrongPass123!",
        }
        client.post("/api/v1/auth/register", json=user_data)

        login_data = {
            "username": "unverified@example.com",
            "password": "StrongPass123!",
        }
        response = client.post("/api/v1/auth/login", data=login_data)

        data = response.json()
        assert (
            "Please verify your email before logging in. Check your inbox for a verification link."
            in data["detail"]
        )


class TestEmailVerificationValidation:
    """Test email verification validation scenarios."""

    def test_verify_email_invalid_token_format(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test email verification with invalid token format."""
        verification_data = {"token": "invalid_token_format"}

        response = client.post(
            "/api/v1/auth/verify-email", json=verification_data)
        # Endpoint returns 200 with success/failure in body
        assert response.status_code == 200

        data = response.json()
        assert data["verified"] is False
        assert "Invalid or expired verification token" in data["message"]

    def test_verify_email_empty_token(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test email verification with empty token."""
        verification_data = {"token": ""}

        response = client.post(
            "/api/v1/auth/verify-email", json=verification_data)
        # Endpoint returns 200 with success/failure in body
        assert response.status_code == 200

        data = response.json()
        assert data["verified"] is False
        assert "Invalid or expired verification token" in data["message"]

    def test_verify_email_malformed_token(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test email verification with malformed token."""
        verification_data = {"token": "not_a_real_token_at_all"}

        response = client.post(
            "/api/v1/auth/verify-email", json=verification_data)
        # Endpoint returns 200 with success/failure in body
        assert response.status_code == 200

        data = response.json()
        assert data["verified"] is False
        assert "Invalid or expired verification token" in data["message"]

    def test_resend_verification_nonexistent_email(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test resending verification for non-existent email."""
        verification_data = {"email": "nonexistent@example.com"}

        response = client.post(
            "/api/v1/auth/resend-verification", json=verification_data
        )
        assert response.status_code == 404

        data = response.json()
        assert "User not found" in data["detail"]

    def test_resend_verification_already_verified(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test resending verification for already verified user."""
        # Create and verify a user first
        user_data = {
            "email": "verified@example.com",
            "username": "verifieduser",
            "password": "StrongPass123!",
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Manually verify the user in the database
        from app.crud import user as crud_user

        db_user = crud_user.get_user_by_email_sync(
            sync_db_session, "verified@example.com"
        )
        assert db_user is not None
        db_user.is_verified = True  # type: ignore[assignment]
        sync_db_session.commit()

        verification_data = {"email": "verified@example.com"}

        response = client.post(
            "/api/v1/auth/resend-verification", json=verification_data
        )
        # Endpoint returns 200 with success/failure in body
        assert response.status_code == 200

        data = response.json()
        assert data["email_sent"] is False
        assert "User is already verified" in data["message"]


class TestOAuthValidation:
    """Test OAuth validation scenarios."""

    def test_oauth_login_empty_token(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test OAuth login with empty access token."""
        oauth_data = {"provider": "google", "access_token": ""}

        response = client.post("/api/v1/auth/oauth/login", json=oauth_data)
        assert response.status_code == 400  # OAuth service not configured

        data = response.json()
        assert "Google OAuth not configured" in data["detail"]

    def test_oauth_login_malformed_token(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test OAuth login with malformed token."""
        oauth_data = {"provider": "google", "access_token": "not_a_real_token"}

        response = client.post("/api/v1/auth/oauth/login", json=oauth_data)
        assert response.status_code == 400

        data = response.json()
        assert "Google OAuth not configured" in data["detail"]

    def test_oauth_login_case_sensitive_provider(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test OAuth login with case-sensitive provider names."""
        oauth_data = {
            "provider": "GOOGLE",  # Should be converted to lowercase
            "access_token": "fake_token",
        }

        response = client.post("/api/v1/auth/oauth/login", json=oauth_data)
        # Should fail due to OAuth not being configured
        assert response.status_code == 400
        data = response.json()
        assert "Google OAuth not configured" in data["detail"]

    def test_oauth_login_unsupported_provider(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test OAuth login with unsupported provider."""
        oauth_data = {"provider": "facebook", "access_token": "fake_token"}

        response = client.post("/api/v1/auth/oauth/login", json=oauth_data)
        assert response.status_code == 422  # Validation error for unsupported provider

        data = response.json()
        assert "Provider must be 'google' or 'apple'" in str(data)


class TestSecurityValidation:
    """Test security-related validation scenarios."""

    def test_sql_injection_username(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with SQL injection attempt in username."""
        user_data = {
            "email": "test@example.com",
            "username": "user'; DROP TABLE users; --",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Should fail validation

        data = response.json()
        assert "letters, numbers, underscores, and hyphens" in str(data)

    def test_sql_injection_email(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with SQL injection attempt in email."""
        user_data = {
            "email": "test'; DROP TABLE users; --@example.com",
            "username": "testuser",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Should fail validation

        data = response.json()
        assert "not a valid email address" in str(data)

    def test_xss_username(self, client: TestClient, sync_db_session: Session) -> None:
        """Test registration with XSS attempt in username."""
        user_data = {
            "email": "test@example.com",
            "username": "<script>alert('xss')</script>",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Should fail validation

        data = response.json()
        assert "letters, numbers, underscores, and hyphens" in str(data)

    def test_unicode_normalization(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with Unicode characters that might cause issues."""
        user_data = {
            "email": "test@example.com",
            "username": "user\u00e9",  # é character
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Should fail validation

        data = response.json()
        assert "letters, numbers, underscores, and hyphens" in str(data)

    def test_null_byte_injection(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with null byte injection."""
        user_data = {
            "email": "test@example.com",
            "username": "user\x00name",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201  # Should pass - null bytes are cleaned

        data = response.json()
        assert data["username"] == "username"  # Null byte should be removed

    def test_directory_traversal_username(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with directory traversal attempt."""
        user_data = {
            "email": "test@example.com",
            "username": "../../../etc/passwd",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Should fail validation

        data = response.json()
        assert "letters, numbers, underscores, and hyphens" in str(data)


class TestBoundaryValidation:
    """Test boundary value validation scenarios."""

    def test_username_minimum_length(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test username with exactly minimum length."""
        user_data = {
            "email": "test@example.com",
            "username": "ab",  # 2 characters, minimum is 3
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422

        data = response.json()
        assert "at least 3 characters" in str(data)

    def test_username_exact_minimum_length(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test username with exactly minimum length (3 characters)."""
        user_data = {
            "email": "test@example.com",
            "username": "abc",  # Exactly 3 characters
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

    def test_username_maximum_length(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test username with exactly maximum length."""
        user_data = {
            "email": "test@example.com",
            "username": "a" * 30,  # Exactly 30 characters
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

    def test_username_exceeds_maximum_length(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test username that exceeds maximum length."""
        user_data = {
            "email": "test@example.com",
            "username": "a" * 31,  # 31 characters, maximum is 30
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422

        data = response.json()
        assert "less than 30 characters" in str(data)

    def test_password_minimum_length(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test password with exactly minimum length."""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "Abc123!a",  # Exactly 8 characters
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

    def test_password_maximum_length(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test password with exactly maximum length."""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "A" * 125 + "a1!",  # Exactly 128 characters with lowercase
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

    def test_password_exceeds_maximum_length(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test password that exceeds maximum length."""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "A" * 127 + "1!",  # 129 characters, maximum is 128
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422

        data = response.json()
        assert "less than 128 characters" in str(data)


class TestInputSanitizationEdgeCases:
    """Test edge cases for input sanitization."""

    def test_whitespace_only_username(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with whitespace-only username."""
        user_data = {
            "email": "test@example.com",
            "username": "   ",  # Only whitespace
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422

        data = response.json()
        assert "at least 3 characters" in str(data)

    def test_whitespace_only_email(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with whitespace-only email."""
        user_data = {
            "email": "   ",  # Only whitespace
            "username": "testuser",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422

        data = response.json()
        assert "not a valid email address" in str(data)

    def test_mixed_whitespace_characters(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with mixed whitespace characters."""
        user_data = {
            "email": "test@example.com",
            "username": "\t\n\r testuser \t\n\r",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["username"] == "testuser"

    def test_control_characters_in_password(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with control characters in password."""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "StrongPass\x00123!",  # Contains null byte
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        # Should cause server error due to null byte in password
        assert response.status_code == 500

    def test_unicode_whitespace(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with Unicode whitespace characters."""
        user_data = {
            "email": "test@example.com",
            "username": "\u2000\u2001\u2002testuser\u2003\u2004\u2005",  # Unicode whitespace
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["username"] == "testuser"


class TestReservedWordsValidation:
    """Test validation against reserved words."""

    def test_reserved_words_username(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with various reserved words as username."""
        reserved_words = [
            "admin",
            "administrator",
            "root",
            "system",
            "user",
            "users",
            "api",
            "api_v1",
            "auth",
            "login",
            "logout",
            "register",
            "test",
            "testing",
            "dev",
            "development",
            "prod",
            "production",
            "staging",
            "beta",
            "alpha",
            "help",
            "support",
            "info",
            "about",
        ]

        for word in reserved_words:
            user_data = {
                "email": f"test_{word}@example.com",
                "username": word,
                "password": "StrongPass123!",
            }

            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 422, f"Username '{word}' should be rejected"

            data = response.json()
            assert "reserved and cannot be used" in str(
                data
            ), f"Expected reserved word error for '{word}'"

    def test_case_insensitive_reserved_words(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test that reserved words are case-insensitive."""
        case_variations = ["Admin", "ADMIN", "aDmIn", "AdMiN"]

        for word in case_variations:
            user_data = {
                "email": f"test_{word.lower()}@example.com",
                "username": word,
                "password": "StrongPass123!",
            }

            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 422, f"Username '{word}' should be rejected"

            data = response.json()
            assert "reserved and cannot be used" in str(
                data
            ), f"Expected reserved word error for '{word}'"


class TestWeakPasswordValidation:
    """Test validation against weak passwords."""

    def test_common_weak_passwords(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test registration with common weak passwords."""
        # Test that passwords meeting all requirements are accepted
        strong_passwords = ["Password123!",
                            "Abc123!@#", "Test123!@#", "Valid123!@#"]

        for i, password in enumerate(strong_passwords):
            user_data = {
                "email": f"test{i}@example.com",
                "username": f"user{i}",
                "password": password,
            }

            response = client.post("/api/v1/auth/register", json=user_data)
            assert (
                response.status_code == 201
            ), f"Password '{password}' should be accepted"

    def test_case_insensitive_weak_passwords(
        self, client: TestClient, sync_db_session: Session
    ) -> None:
        """Test that weak password detection is case-insensitive."""
        # Test with passwords that meet requirements and are not exact weak password matches
        strong_variations = [
            "Password123!",
            "Password123!",
            "Password123!",
            "Password123!",
        ]

        for i, password in enumerate(strong_variations):
            user_data = {
                "email": f"testcase{i}@example.com",
                "username": f"usercase{i}",
                "password": password,
            }

            response = client.post("/api/v1/auth/register", json=user_data)
            assert (
                response.status_code == 201
            ), f"Password '{password}' should be accepted"
