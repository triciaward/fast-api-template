from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Test authentication API endpoints."""

    def test_register_user_success(self, client: TestClient, test_user_data: dict[str, str]) -> None:
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 200
        data = response.json()

        # Check response contains expected fields
        assert "id" in data
        assert "email" in data
        assert "username" in data
        assert "date_created" in data
        # Password should not be in response
        assert "password" not in data
        assert "hashed_password" not in data

        # Check values match input
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]

    def test_register_user_duplicate_email(self, client: TestClient, test_user_data: dict[str, str]) -> None:
        """Test registration with duplicate email."""
        # Create user first via API
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 200

        # Try to register with same email
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_register_user_duplicate_username(self, client: TestClient, test_user_data: dict[str, str], test_user_data_2: dict[str, str]) -> None:
        """Test registration with duplicate username."""
        # Create user first via API
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 200

        # Try to register with same username but different email
        duplicate_username_data = test_user_data_2.copy()
        duplicate_username_data["username"] = test_user_data["username"]

        response = client.post("/api/v1/auth/register",
                               json=duplicate_username_data)

        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]

    def test_register_user_invalid_email(self, client: TestClient, test_user_data: dict[str, str]) -> None:
        """Test registration with invalid email format."""
        invalid_data = test_user_data.copy()
        invalid_data["email"] = "invalid-email"

        response = client.post("/api/v1/auth/register", json=invalid_data)

        assert response.status_code == 422
        # Pydantic validation error for invalid email

    def test_register_user_missing_fields(self, client: TestClient) -> None:
        """Test registration with missing required fields."""
        incomplete_data = {"email": "test@example.com"}

        response = client.post("/api/v1/auth/register", json=incomplete_data)

        assert response.status_code == 422
        # Pydantic validation error for missing fields

    def test_login_success(self, client: TestClient, test_user_data: dict[str, str]) -> None:
        """Test successful user login."""
        # Create user first via API
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 200

        # Login with correct credentials
        login_data = {
            # FastAPI OAuth2 uses 'username' field for email
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }

        response = client.post("/api/v1/auth/login", data=login_data)

        assert response.status_code == 200
        data = response.json()

        # Check response contains token
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client: TestClient, test_user_data: dict[str, str]) -> None:
        """Test login with wrong password."""
        # Create user first via API
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 200

        # Try to login with wrong password
        login_data = {
            "username": test_user_data["email"],
            "password": "wrongpassword"
        }

        response = client.post("/api/v1/auth/login", data=login_data)

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_wrong_email(self, client: TestClient, test_user_data: dict[str, str]) -> None:
        """Test login with wrong email."""
        # Create user first via API
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 200

        # Try to login with wrong email
        login_data = {
            "username": "wrong@example.com",
            "password": test_user_data["password"]
        }

        response = client.post("/api/v1/auth/login", data=login_data)

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient) -> None:
        """Test login for non-existent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "anypassword"
        }

        response = client.post("/api/v1/auth/login", data=login_data)

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_missing_credentials(self, client: TestClient) -> None:
        """Test login with missing credentials."""
        response = client.post("/api/v1/auth/login", data={})

        assert response.status_code == 422
        # Validation error for missing required fields
