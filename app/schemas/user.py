import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str
    is_superuser: bool = False


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: uuid.UUID
    is_superuser: bool
    is_verified: bool
    date_created: datetime
    oauth_provider: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# OAuth schemas
class OAuthLogin(BaseModel):
    provider: str  # 'google' or 'apple'
    access_token: str


class OAuthUserInfo(BaseModel):
    provider: str
    oauth_id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None


# Email verification schemas
class EmailVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationResponse(BaseModel):
    message: str
    email_sent: bool


class VerifyEmailRequest(BaseModel):
    token: str


class VerifyEmailResponse(BaseModel):
    message: str
    verified: bool
