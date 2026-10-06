from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    """
    A valid user account model with valid email and minimum 8 char length password
    """
    email:EmailStr
    password:str=Field(min_length=8)