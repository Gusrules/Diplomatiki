import re
from pydantic import BaseModel
from pydantic import EmailStr, Field, field_validator

class LoginIn(BaseModel):
    email: str
    password: str

class LoginOut(BaseModel):
    user_id: int
    role: str
    name: str
    token: str

class MeOut(BaseModel):
    user_id: int
    role: str
    name: str

class RegisterStudentIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

    @field_validator("password")
    @classmethod
    
    def strong_password(cls, v: str):
        # requirements (διάλεξε αυτά που θες)
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least 1 uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least 1 lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least 1 number.")
        # προαιρετικό:
        # if not re.search(r"[!@#$%^&*()_\-+=\[\]{};:'\",.<>/?\\|`~]", v):
        #     raise ValueError("Password must contain at least 1 symbol.")
        return v

class RegisterStudentOut(BaseModel):
    user_id: int
    role: str
    name: str

class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str

class ChangePasswordOut(BaseModel):
    ok: bool
