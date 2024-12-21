from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List
from app.models import MenuItem, Order, OrderStatus # Importar modelos MenuItem, Order y OrderStatus

from sqlmodel import Session, select
from app.db import init_db, get_session

# Crear instancia de FastAPI
app = FastAPI()

# Inicializar base de datos al iniciar la aplicación
@app.on_event("startup")
def on_startup():
    init_db()


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
def get_orders(session: Session = Depends(get_session)):
    """Obtener todas las órdenes."""
    resultItems = session.exec(select(Order)).all()
    return resultItems


@app.post("/orders/", response_model=Order)
def create_order(order: Order, session: Session = Depends(get_session)):
    """Crear una nueva orden."""
    session.add(order)
    session.commit()
    session.refresh(order)

    # Calcular total con base en los ítems del menú
    #total = 0
    #for item_id in order.items:
    #    item = next((item for item in menu_db if item.id == item_id), None)
    #    if not item:
    #        raise HTTPException(status_code=404, detail=f"Item con ID {item_id} no encontrado")
    #    total += item.price
    #order.total = total
    #order_db.append(order)
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

