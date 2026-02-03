from pydantic import BaseModel

class LoginIn(BaseModel):
    role: str
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
