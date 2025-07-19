import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)

    # OAuth fields
    # 'google', 'apple', or None
    oauth_provider = Column(String, nullable=True)
    oauth_id = Column(String, nullable=True)  # OAuth provider's user ID
    oauth_email = Column(String, nullable=True)  # Email from OAuth provider

    # Email verification
    verification_token = Column(String, nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username}, is_superuser={self.is_superuser}, is_verified={self.is_verified})>"
