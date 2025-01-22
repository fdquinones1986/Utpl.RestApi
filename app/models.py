from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from pydantic import BaseModel, EmailStr

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
    id: Optional[int]
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


#clases para el manejo de pedidos
class OrderItemLink(SQLModel, table=True):
    order_id: int = Field(foreign_key="order.id", primary_key=True)
    menu_item_id: int = Field(foreign_key="menuitem.id", primary_key=True)

class MenuItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    price: float
    orders: List["Order"] = Relationship(back_populates="items", link_model=OrderItemLink)

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_name: str
    status: str = "pending"
    total: Optional[float] = 0
    items: List[MenuItem] = Relationship(back_populates="orders", link_model=OrderItemLink)
    

MenuItem.orders = Relationship(back_populates="items", link_model=OrderItemLink)

class OrderStatus(BaseModel):
    status: str = "pending"

