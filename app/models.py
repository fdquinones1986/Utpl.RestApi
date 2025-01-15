from sqlmodel import SQLModel, Field
from typing import Optional, List
from pydantic import BaseModel


class MenuItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    price: float

# ajustada para SQLModel en lugar de Pydantic


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    #items: List[int]  # Lista de IDs de los elementos del menú
    total: float
    customer_name: str
    status: str = "pending"


class OrderStatus(BaseModel):
    status: str = "pending"
