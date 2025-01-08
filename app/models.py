from sqlmodel import SQLModel, Field
from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr

from datetime import datetime, date


class Orden(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    producto: str
    cantidad: float
    tipo: str
    precio: float
    total: float


class OrdenActualizacion(BaseModel):
    precio: Optional[float] = None,
    cantidad: Optional[float] = None

# Clases para el manejo de usuarios


class GetUser(BaseModel):
    email: EmailStr
    username: Optional[str]
    role: str

    class Config:
        orm_mode = True
        use_enum_values = True


class LoginUser(BaseModel):
    email: EmailStr
    password: str

    class Config:
        orm_mode = True
        use_enum_values = True


class PostUser(BaseModel):
    email: EmailStr
    username: Optional[str]
    password: str

    class Config:
        orm_mode = True
        use_enum_values = True


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: str = Field(default="user")


class Token(SQLModel, table=True):
    id: int = Field(primary_key=True, index=True)
    token: str = Field(index=True)
    user_id: int
