import re


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if len(password) > 128:
        return False, "Password must be less than 128 characters"

    # Check for at least one uppercase letter
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    # Check for at least one lowercase letter
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    # Check for at least one digit
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"

    # Check for at least one special character
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        return (
            False,
            "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)",
        )

    # Check for common weak passwords
    weak_passwords = {
        "password",
        "123456",
        "12345678",
        "qwerty",
        "abc123",
        "password123",
        "admin",
        "letmein",
        "welcome",
        "monkey",
        "dragon",
        "master",
    }
    if password.lower() in weak_passwords:
        return False, "Password is too common, please choose a stronger password"

    return True, ""


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate username format and content.

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"

    if len(username) > 30:
        return False, "Username must be less than 30 characters"

    # Check for valid characters (alphanumeric, underscore, hyphen)
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return (
            False,
            "Username can only contain letters, numbers, underscores, and hyphens",
        )

    # Check that username doesn't start or end with special characters
    if username.startswith("_") or username.startswith("-"):
        return False, "Username cannot start with underscore or hyphen"

    if username.endswith("_") or username.endswith("-"):
        return False, "Username cannot end with underscore or hyphen"

    # Check for consecutive special characters
    if re.search(r"[_-]{2,}", username):
        return False, "Username cannot contain consecutive underscores or hyphens"

    # Check for reserved words
    reserved_words = {
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
    }
    if username.lower() in reserved_words:
        return False, "Username is reserved and cannot be used"

    return True, ""


def clean_input(text: str) -> str:
    """
    Clean user input by removing control characters and trimming whitespace.
    Does NOT truncate length - use validate_username for length validation.

    Args:
        text: Input text to clean

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove null bytes and control characters
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

    # Trim whitespace
    text = text.strip()

    return text


def sanitize_input(text: str, max_length: int = 100) -> str:
    """
    Sanitize user input to prevent injection attacks.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove null bytes and control characters
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

    # Trim whitespace
    text = text.strip()

    # Limit length
    if len(text) > max_length:
        text = text[:max_length]

    return text


def validate_email_format(email: str) -> tuple[bool, str]:
    """
    Additional email validation beyond Pydantic's EmailStr.

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # Basic format check (Pydantic EmailStr handles most of this)
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        return False, "Invalid email format"

    # Check for disposable email domains (basic list)
    disposable_domains = {
        "10minutemail.com",
        "guerrillamail.com",
        "tempmail.org",
        "mailinator.com",
        "throwaway.email",
        "temp-mail.org",
    }

    domain = email.split("@")[1].lower()
    if domain in disposable_domains:
        return False, "Disposable email addresses are not allowed"

    return True, ""
