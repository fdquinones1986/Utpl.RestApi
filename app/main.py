from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Annotated
from sqlmodel import Session, select

from app.models import MenuItem, Order, OrderStatus, OrderItemLink, GetUser, PostUser, User
from app.db import init_db, get_session
from app.utils.auth import decodeJWT, get_user_by_email, create_user, create_access_token
from app.utils.passwords import verify_pwd
from app.utils.telegram_service import send_message_telegram
from app.utils.email_service import send_email

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

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
              version="0.1.0", contact={"name": "Nicole Calvas", "email":"nacalvas@utpl.edu.ec"}, openapi_tags=tags_metadata)

# Inicializa la base de datos al iniciar la aplicación
@app.on_event("startup")
def on_startup():
    init_db()
    
# Ruta de bienvenida
@app.get("/", tags=["Welcome"])
def read_root():
    return {"message": "Bienvenido a la API de Come en Casa"}


# Gestión de Usuarios
@app.post("/register", response_model=GetUser, tags=["users"])
def register_user(payload: PostUser, session: Session = Depends(get_session)):
    user = get_user_by_email(session, payload.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El usuario con el email {payload.email} ya existe.",
        )
    user = create_user(session, payload)
    return user


@app.post("/token", tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = get_user_by_email(session, form_data.username)
    if not user or not verify_pwd(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token,"token_type": "bearer"}


@app.get("/users", response_model=List[GetUser], tags=["users"])
def get_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users


@app.delete("/users/{user_id}", tags=["users"])
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    session.delete(user)
    session.commit()
    return {"message": "Usuario eliminado correctamente"}


# Gestión del Menú
@app.get("/menu/", response_model=List[MenuItem], tags=["menu"])
def get_menu(session: Session = Depends(get_session)):
    menu_items = session.exec(select(MenuItem)).all()
    return menu_items


@app.post("/menu/", response_model=MenuItem, tags=["menu"])
def add_menu_item(item: MenuItem, session: Session = Depends(get_session)):
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@app.delete("/menu/{item_id}", tags=["menu"])
def delete_menu_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    session.delete(item)
    session.commit()
    return {"message": "Ítem eliminado correctamente"}


# Gestión de Órdenes
@app.get("/orders/", response_model=List[Order], tags=["orders"])
def get_orders(session: Session = Depends(get_session)):
    orders = session.exec(select(Order)).all()
    return orders


@app.post("/orders/", response_model=Order, tags=["orders"])
def create_order(order_data: dict, session: Session = Depends(get_session)):
    order = Order(customer_name=order_data["customer_name"], status="pending", total=0)
    total = 0

    for item_id in order_data["items"]:
        item = session.get(MenuItem, item_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"Ítem con ID {item_id} no encontrado")
        total += item.price
        order_item_link = OrderItemLink(order_id=order.id, menu_item_id=item_id)
        session.add(order_item_link)

    order.total = total
    session.add(order)
    session.commit()
    session.refresh(order)

    send_message_telegram(f"Se ha creado una nueva orden: {order.id}")
    send_email("Nueva orden", f"Orden creada: {order.id}", ["admin@example.com"])
    return order


@app.put("/orders/{order_id}", tags=["orders"])
def update_order_status(order_id: int, status_update: OrderStatus, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    order.status = status_update.status
    session.add(order)
    session.commit()
    session.refresh(order)
    return order