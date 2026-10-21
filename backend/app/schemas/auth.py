from pydantic import BaseModel, EmailStr, Field


# User registration request
class UserRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


# User login request
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Public user information
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True


# Token response after successful login
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse