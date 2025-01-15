from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi import FastAPI, HTTPException, Depends, Query, status
from pydantic import BaseModel
from typing import List, Annotated

# Importar modelos MenuItem, Order y OrderStatus
from app.models import MenuItem, Order, OrderStatus

from sqlmodel import Session, select
from app.db import init_db, get_session

from app.security import verification
#Trabajar con telegra
from app.utils.telegram_service import send_message_telegram


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa la base de datos al iniciar la app
    init_db()
    yield
    # Puedes añadir lógica de limpieza aquí (opcional)

# Crea la instancia de FastAPI con el ciclo de vida
app = FastAPI(lifespan=lifespan)

def bienvenida():
    return {'mensaje': 'Bienvenidos a la API de Come en Casa'}

# Rutas para gestión de Menú

# Ruta para obtener todos los ítems del menú
@app.get("/menu/", response_model=List[MenuItem])
def get_menu(session: Session = Depends(get_session), Verification=Depends(verification)):
    """Obtener todos los ítems del menú desde la base de datos."""
    menu_items = session.exec(select(MenuItem)).all()
    return menu_items


# Ruta para añadir un ítem al menú
@app.post("/menu/", response_model=MenuItem)
def add_menu_item(item: MenuItem, session: Session = Depends(get_session), Verification=Depends(verification)):
    """Añadir un ítem al menú."""
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@app.delete("/menu/{item_id}")  # Ruta para eliminar un ítem del menú
def delete_menu_item(item_id: int, session: Session = Depends(get_session), Verification=Depends(verification)):
    """Eliminar un ítem del menú por ID."""
    item = session.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    session.delete(item)
    session.commit()
    return {"message": "Ítem eliminado exitosamente"}


# Rutas para gestión de Órdenes

@app.get("/orders/", response_model=List[Order])
def get_orders(session: Session = Depends(get_session), Verification=Depends(verification)):
    """Obtener todas las órdenes."""
    resultItems = session.exec(select(Order)).all()
    return resultItems


@app.post("/orders/", response_model=Order)
async def create_order(order: Order, session: Session = Depends(get_session), Verification=Depends(verification)):
    """Crear una nueva orden."""
    session.add(order)
    session.commit()
    session.refresh(order)

   # Calcular total con base en los ítems del menú
    '''total = 0
    for item_id in order.items:
        # Buscar el ítem en el menú
        item = session.query(MenuItem).filter(MenuItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"Item con ID {item_id} no encontrado")
        total += item.price

    # Asignar el total al pedido
    order.total = total'''

    # Agregar y guardar en la base de datos
    session.add(order)
    session.commit()
    session.refresh(order)

    await send_message_telegram(f"Se ha creado una nueva orden con el id: {order.id} y precio: {order.total} para el cliente: {order.customer_name} con el estado del pedido: {order.status}")

    return order


@app.put("/orders/{order_id}")
def update_order_status(order_id: int, order_i: OrderStatus, session: Session = Depends(get_session), Verification=Depends(verification)):
    """Actualizar el estado de una orden."""
    itemDB = session.get(Order, order_id)
    if itemDB is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if order_i.precio is not None:
        itemDB.precio = order_i.precio
    if order_i.cantidad is not None:
        itemDB.cantidad = order_i.cantidad
    session.add(itemDB)
    session.commit()
    session.refresh(itemDB)
    return order_i

# Ruta de bienvenida


@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Come en Casa"}
