from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100, examples=["Olena"])
    last_name: str = Field(min_length=1, max_length=100, examples=["Shevchenko"])
    email: EmailStr = Field(examples=["olena@example.com"])
    phone: str = Field(min_length=5, max_length=30, examples=["+380501234567"])
    birthday: date = Field(examples=["1995-05-17"])
    additional_data: str | None = Field(default=None, examples=["Friend from university"])


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=5, max_length=30)
    birthday: date | None = None
    additional_data: str | None = None


class ContactResponse(ContactBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr = Field(examples=["user@example.com"])
    password: str = Field(min_length=6, examples=["secretpassword"])


class UserLogin(BaseModel):
    email: EmailStr = Field(examples=["user@example.com"])
    password: str = Field(examples=["secretpassword"])


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    avatar: str | None
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr


