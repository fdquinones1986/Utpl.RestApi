from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from enum import Enum 

# Clases para el manejo de usuarios
class GetUser(BaseModel): #Obtener todos los usuarios
    email: EmailStr
    username: Optional[str]
    role: str

    class Config:
        orm_mode = True
        use_enum_values = True


class LoginUser(BaseModel): #Iniciar sesion
    email: EmailStr
    password: str

    class Config:
        orm_mode = True
        use_enum_values = True


class PostUser(BaseModel): #Registrar un usuario
    id: Optional[int]
    email: EmailStr
    username: Optional[str]
    password: str

    class Config:
        orm_mode = True
        use_enum_values = True


class User(SQLModel, table=True): #Guarda a los usuarios
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: str = Field(default="user")


class Token(SQLModel, table=True): #Guarda los tokens
    id: int = Field(primary_key=True, index=True)
    token: str = Field(index=True)
    user_id: int


#Clases para el manejo de pedidos

class OrderItemLink(SQLModel, table=True):#Guarda los items de los pedidos
    order_id: int = Field(foreign_key="order.id", primary_key=True)
    menu_item_id: int = Field(foreign_key="menuitem.id", primary_key=True)

class MenuItem(SQLModel, table=True): #Guarda los items del menu
    id: int = Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    name: str
    description: str
    price: float
    orders: List["Order"] = Relationship(back_populates="items", link_model=OrderItemLink)

class Order(SQLModel, table=True): #Guarda los pedidos
    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    customer_name: str
    status: str = "pending"
    total: Optional[float] = 0
    items: List[MenuItem] = Relationship(back_populates="orders", link_model=OrderItemLink)
    

MenuItem.orders = Relationship(back_populates="items", link_model=OrderItemLink) #Relacion entre menuitem y order

class OrderStatus(BaseModel): #Cambia el estado de un pedido
    status: str 

class StatusEnum(str, Enum):
    pending = "pendiente"
    processing = "en proceso"
    completed = "completado"
    delivered = "entregado"
    canceled = "cancelado"

class OrderStatus(BaseModel):
    status: StatusEnum

