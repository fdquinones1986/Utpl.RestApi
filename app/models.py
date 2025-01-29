from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr
from datetime import datetime, date

from enum import Enum

# Clases para el manejo de pedidos


class OrderItemLink(SQLModel, table=True):  # Guarda los items de los pedidos
    id: int = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    menu_item_id: int = Field(foreign_key="menuitem.id")


class MenuItem(SQLModel, table=True):  # Guarda los items del menu
    id: int = Field(default=None, primary_key=True,
                    sa_column_kwargs={"autoincrement": True})
    name: str
    description: str
    price: float
    orders: List["Order"] = Relationship(
        back_populates="items", link_model=OrderItemLink)


class StatusEnum(str, Enum):
    pending = "pendiente"
    processing = "en proceso"
    completed = "completado"
    delivered = "entregado"
    canceled = "cancelado"


class Order(SQLModel, table=True):  # Guarda los pedidos
    id: int = Field(default=None, primary_key=True,
                    sa_column_kwargs={"autoincrement": True})
    customer_name: str
    status: StatusEnum = Field(default=StatusEnum.pending)
    total: Optional[float] = 0
    items: List[MenuItem] = Relationship(
        back_populates="orders", link_model=OrderItemLink)


# Relacion entre menuitem y order
MenuItem.orders = Relationship(
    back_populates="items", link_model=OrderItemLink)

# Clases para el manejo de usuarios


class GetUser(BaseModel):  # Obtener todos los usuarios
    id: Optional[int]
    email: EmailStr
    username: Optional[str]
    role: str

    class Config:
        orm_mode = True
        use_enum_values = True


class LoginUser(BaseModel):  # Iniciar sesion
    email: EmailStr
    password: str

    class Config:
        orm_mode = True
        use_enum_values = True


class PostUser(BaseModel):  # Registrar un usuario
    email: EmailStr
    username: Optional[str]
    password: str

    class Config:
        orm_mode = True
        use_enum_values = True


class User(SQLModel, table=True):  # Guarda a los usuarios
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    phone: Optional[int] = Field(default=None)
    hashed_password: str
    role: str = Field(default="user")


class Token(SQLModel, table=True):  # Guarda los tokens
    id: int = Field(primary_key=True, index=True)
    token: str = Field(index=True)
    user_id: int = Field(foreign_key="user.id")


# Datos para el manejo en controladores
class MenuItemCreate(BaseModel):  # Guarda los items del menu
    name: str
    description: str
    price: float


class OrderCreate(BaseModel):  # Guarda los pedidos
    customer_name: str
    status: StatusEnum = StatusEnum.pending
    items: List[int]
