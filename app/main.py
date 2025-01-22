from fastapi import FastAPI, Depends, HTTPException, Query, status
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Annotated


# Importar modelos MenuItem, Order, OrderStatus y User
from app.models import MenuItem, Order, OrderStatus, OrderItemLink, GetUser, PostUser, User

from sqlmodel import Session, select
from app.db import init_db, get_session

from app.security import verification

#Autenticacion y autorizacion JWT y oauth2
from app.utils.auth import decodeJWT, get_user, create_user, create_access_token, create_refresh_token, JWTBearer
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import date, datetime, timedelta, time

from app.utils.passwords import verify_pwd

# Trabajar con telegram
from app.utils.telegram_service import send_message_telegram

# Trabajar con email
from app.utils.email_service import send_email


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa la base de datos al iniciar la app
    init_db()
    yield
########### Puedes añadir lógica de limpieza aquí (opcional)
tags_metadata = [
    {
        "name": "menu",
        "description": "Operaciones relacionadas con el menú de Come en Casa",
    },
    {
        "name": "orders",
        "description": "Operaciones relacionadas con las órdenes de Come en Casa",
    },
    {
        "name": "users",
        "description": "Operaciones relacionadas con los usuarios de Come en Casa",
    },
]

# Crea la instancia de FastAPI con el ciclo de vida
app = FastAPI(lifespan=lifespan, title="API de Come en Casa", description="API para la gestión de pedidos de Come en Casa",
              version="0.1.0", contact={"name": "Nicole Calvas", "email":"nacalvas@utpl.edu.ec"}, openapi_tags=tags_metadata)


def bienvenida():
    return {'mensaje': 'Bienvenidos a la API de Come en Casa'}


# Rutas para gestión de Usuarios
def get_user_by_id(user_id: int, db: Session) -> User:
    """
    Get a user by ID
    """
    return db.query(User).filter(User.id == user_id).first()
    # return db.exec(User).filter(User.id == user_id).first()


def get_current_user(token: str = Depends(JWTBearer()), session: Session = Depends(get_session)) -> User:
    """
    Get current user from JWT token
    """
    payload = decodeJWT(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or expired token",
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or expired token",
        )
    # Assuming you have a function to get user by id from the database
    user = get_user_by_id(user_id, session)  # Implement this function
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@app.on_event("startup")
def on_startup():
    init_db()

#Ruta para regitrar un usuario
@ app.post("/register", response_model=GetUser, tags=["usuarios"])
def register_user(payload: PostUser, session: Session = Depends(get_session)):
    if not payload.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please add Email",
        )
    user = get_user(session, payload.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User with email {payload.email} already exists",
        )
    user = create_user(session, payload)
    print(user)
    return user
#Ruta para iniciar sesion
@ app.post("/login", response_model=GetUser, tags=["usuarios"])
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = get_user(session, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect username or password",
        )
    if not verify_pwd(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(user.id)
    return {"access_token": access_token, "token_type": "bearer"}

#Ruta para obtener todos los usuarios
@ app.get("/users", response_model=List[GetUser], tags=["usuarios"])
def get_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users
#Ruta para obtener eliminar un usuario
@ app.delete("/users/{user_id}", tags=["usuarios"])
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user = get_user_by_id(user_id, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    session.delete(user)
    session.commit()
    return {"message": "User deleted successfully"}



# Rutas para gestión de Menú
# Ruta para obtener todos los ítems del menú
@app.get("/menu/", response_model=List[MenuItem], tags=["menu"])
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
async def create_order(order_data: dict, session: Session = Depends(get_session)):
    """Crear una nueva orden."""
    # Crear un pedido vacío
    order = Order(customer_name=order_data["customer_name"], status="pending", total=0)

    # Asociar los ítems del pedido
    total = 0
    for item_id in order_data["items"]:
        item = session.query(MenuItem).filter(MenuItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"Item con ID {item_id} no encontrado")
        total += item.price
        order.items.append(item)

    # Asignar el total y guardar
    order.total = total
    session.add(order)
    session.commit()
    session.refresh(order)

    await send_message_telegram(f"Se ha creado una nueva orden con el id: {order.id} y precio: {order.total} para el cliente: {order.customer_name} con el estado del pedido: {order.status}")
    send_email("Confirmación de orden", f"Se ha creado una nueva orden con el id: {order.id} y precio: {order.total} para el cliente: {order.customer_name} con el estado del pedido: {order.status}", [
               "nacalvas@utpl.edu.ec"])
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
