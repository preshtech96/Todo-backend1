from pydantic import BaseModel,EmailStr
from typing import Optional





class User(BaseModel):
    email: EmailStr
    password: Optional[str] = None
    confirmPassword: Optional[str] = None
    phone: Optional[str] = None
    firstname: str
    lastname: str
    secretpin: Optional[str] = None
    


class Login(BaseModel):
    email: EmailStr
    password: str



class Secret(BaseModel):
    id: Optional[str] = None
    secretpin: Optional[str] = None


class Todo(BaseModel):
    title: str
    description: str = ""
    userId: str
    status:bool=False

    

    