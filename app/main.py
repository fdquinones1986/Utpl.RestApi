from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Annotated

from app.models import MenuItem, MenuItemCreate, Order, OrderItemLink, GetUser, PostUser, User, OrderCreate
from sqlmodel import Session, select
from app.db import init_db, get_session

from app.security import verification

from app.utils.auth import decodeJWT, get_user, create_access_token, create_user, create_refresh_token, JWTBearer
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import date, datetime, timedelta, time

from app.utils.passwords import verify_pwd

# para trabajar con telegram
from app.utils.telegram_service import send_message_telegram

# para trabajar con email
from app.utils.email_service import send_email

# para trabajar con fastapi versioning
from fastapi_versioning import VersionedFastAPI, version


# Configuración de OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

tags_metadata = [
    {
        "name": "Welcome",
        "description": "Mensaje de biendvenida a la API de Come en Casa",
    },
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
    {
        "name": "Auth",
        "description": "Operaciones de autenticación y autorización",
    }
]

# Crea la instancia de FastAPI con el ciclo de vida
app = FastAPI(title="API de Come en Casa", description="API para la gestión de pedidos de Come en Casa",
              version="0.1.0", contact={"name": "Nicole Calvas", "email": "nacalvas@utpl.edu.ec"}, openapi_tags=tags_metadata)


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
    user = get_user_by_id(user_id, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


# Comienza API de Come en Casa
# Inicializa la base de datos al iniciar la aplicación
@app.on_event("startup")
def on_startup():
    init_db()

# Ruta de bienvenida


@app.get("/", tags=["Welcome"])
def read_root():
    return {"message": "Bienvenido a la API de Come en Casa"}


# Gestión de Usuarios
# Ruta para obtener todos los usuarios
@app.get("/users", response_model=List[GetUser], tags=["users"])
def list_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

# Ruta para registrar un usuario


@app.post("/register", response_model=GetUser, tags=["users"])
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

# Ruta para iniciar sesión


@ app.post("/login", tags=["users"])
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    """
    Login user based on email and password
    """
    user = get_user(db, form_data.username)
    if not user or not verify_pwd(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token({"userid": user.id, "username": user.username}, timedelta(minutes=30))
    refresh = create_refresh_token(user.id, timedelta(minutes=1008))

    return {'access_token': token, 'token_type': 'bearer', 'refresh_token': refresh, "user_id": user.id}

# Ruta para obtener los detalles del usuario actual


@ app.get("/users/me", response_model=GetUser, tags=["users"])
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user details
    """
    return current_user

# Ruta para elminar un usuario


@app.delete("/users/{user_id}", tags=["users"])
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    session.delete(user)
    session.commit()
    return {"message": "Usuario eliminado correctamente"}


# Comienza gestión interna restaurante

# Gestión del Menú
# obtener todo el menu
@app.get("/menu/", response_model=List[MenuItem], tags=["menu"])
def get_menu(session: Session = Depends(get_session), Verification=Depends(verification)):
    menu_items = session.exec(select(MenuItem)).all()
    return menu_items

# Ruta para agregar un item al menu


@app.post("/menu/", response_model=MenuItem, tags=["menu"])
async def add_menu_item(item: MenuItemCreate, session: Session = Depends(get_session)):
    itemDb  = MenuItem(**item.model_dump())
    session.add(itemDb)
    session.commit()
    session.refresh(itemDb)

    await send_message_telegram(f"Se ha creado un nuevo item en el menú con el id: {itemDb.id} y nombre: {itemDb.name} con la sigiente descripción: {itemDb.description} y precio: {itemDb.price}")
    send_email("Confirmación de item en el menú", f"Se ha creado un nuevo item en el menú con el id: {itemDb.id} y nombre: {itemDb.name} con la sigiente descripción: {itemDb.description} y precio: {itemDb.price}", [
               "ncwork.350@outlook.com"])
    return itemDb

# Ruta para eliminar un item del menu


@app.delete("/menu/{item_id}", tags=["menu"])
async def delete_menu_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    session.delete(item)
    session.commit()

    await send_message_telegram(f"Se ha eliminado un item en el menú con el id: {item.id} y nombre: {item.name} con la siguiente descripción: {item.description} y precio: {item.price}")
    send_email("Confirmación de item en el menú", f"Se ha eliminado un item en el menú con el id: {item.id} y nombre: {item.name} con la siguiente descripción: {item.description} y precio: {item.price}", [
               "ncwork.350@outlook.com"])
    return {"message": "Ítem eliminado correctamente"}

# Gestión de Órdenes

# Ruta para obtener todas las ordenes


@app.get("/orders/", response_model=List[Order], tags=["orders"])
def get_orders(session: Session = Depends(get_session)):
    orders = session.exec(select(Order)).all()
    return orders

# Ruta para crear una nueva orden


@app.post("/orders/", response_model=Order, tags=["orders"])
async def create_order(order: OrderCreate, session: Session = Depends(get_session)):
    orderDb = Order(**order.model_dump())
    session.add(orderDb)
    session.commit()
    session.refresh(orderDb)

    await send_message_telegram(f"Se ha creado una nueva orden con el id: {orderDb.id} a nombre de: {order.customer_name} con el estado de: {order.status} y total de: {order.total}")
    send_email("Confirmación de orden", f"Se ha creado una nueva orden con el id: {order.id} a nombre de: {order.customer_name} con el estado de: {order.status} y total de: {order.total}", [
               "ncwork.350@outlook.com"])
    return orderDb


# Ruta para actualizar el estado de una orden
@app.put("/orders/{order_id}", tags=["orders"])
async def update_order_status(order_id: int, status_update: Order, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    order.status = status_update.status
    session.add(order)
    session.commit()
    session.refresh(order)

    await send_message_telegram(f"Se ha actualizado una orden con el id: {Order.id} a nombre de: {Order.customer_name} con el estado de: {Order.status} y total de: {Order.total}")
    send_email("Actualización de orden", f"Se ha actualizado una orden con el id: {Order.id} a nombre de: {Order.customer_name} con el estado de: {Order.status} y total de: {Order.total}", [
               "ncwork.350@outlook.com"])
    return order("Orden Actualizada Correctamente")
