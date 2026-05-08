from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    name: str
    is_active: bool | None = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = None
    is_active: bool | None = None

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

class UserListItemResponse(UserResponse):
    pass