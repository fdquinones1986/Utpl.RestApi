from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
import uvicorn

# Crear instancia de FastAPI
app = FastAPI()

# Modelos Pydantic para validación de datos


class MenuItem(BaseModel):
    id: int
    name: str
    price: float
    description: str


class Order(BaseModel):
    id: int
    items: List[int]  # Lista de IDs de los elementos del menú
    total: float
    customer_name: str
    status: str = "pending"


class OrderStatus(BaseModel):
    status: str = "pending"


# Base de datos simulada
menu_db = []
order_db = []

# Rutas para gestión de Menú


@app.get("/menu/", response_model=List[MenuItem])
def get_menu():
    """Obtener todos los ítems del menú."""
    return menu_db


@app.post("/menu/", response_model=MenuItem)
def add_menu_item(item: MenuItem):
    """Añadir un ítem al menú."""
    menu_db.append(item)
    return item


@app.delete("/menu/{item_id}")
def delete_menu_item(item_id: int):
    """Eliminar un ítem del menú por ID."""
    global menu_db
    menu_db = [item for item in menu_db if item.id != item_id]
    return {"message": "Ítem eliminado exitosamente"}

# Rutas para gestión de Órdenes


@app.get("/orders/", response_model=List[Order])
def get_orders():
    """Obtener todas las órdenes."""
    return order_db


@app.post("/orders/", response_model=Order)
def create_order(order: Order):
    """Crear una nueva orden."""
    # Calcular total con base en los ítems del menú
    total = 0
    for item_id in order.items:
        item = next((item for item in menu_db if item.id == item_id), None)
        if not item:
            raise HTTPException(status_code=404, detail=f"Item con ID {
                                item_id} no encontrado")
        total += item.price
    order.total = total
    order_db.append(order)
    return order


@app.put("/orders/{order_id}")
def update_order_status(order_id: int, order_i: OrderStatus):
    """Actualizar el estado de una orden."""
    for order in order_db:
        if order.id == order_id:
            order.status = order_i.status
            return order
    raise HTTPException(status_code=404, detail="Orden no encontrada")

# Ruta de bienvenida


@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Come en Casa"}

#Configuración para Render

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
