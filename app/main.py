from fastapi import FastAPI, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Annotated

from app.models import Orden, OrdenActualizacion, GetUser, PostUser, User
from sqlmodel import Session, select
from app.db import init_db, get_session

from app.security import verification

from app.utils.auth import decodeJWT, get_user, create_user, create_access_token, create_refresh_token, JWTBearer
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import date, datetime, timedelta, time

from app.utils.passwords import verify_pwd

# para trabajar con telegram
from app.utils.telegram_service import send_message_telegram

# para trabajar con email
from app.utils.email_service import send_email

# para trabajar con fastapi versioning
from fastapi_versioning import VersionedFastAPI, version

tags_metadata = [
    {
        "name": "usuarios",
        "description": "Operaciones con usuarios. El **login** logica esta disponible aqui.",
    },
    {
        "name": "ordenes",
        "description": "Administracion de ordenes.",
        "externalDocs": {
            "description": "Items external docs",
            "url": "https://fastapi.tiangolo.com/",
        },
    },
]

app = FastAPI(title="FastAPI Utpl 2025",
              description="API para el manejo de ordenes de compra",
              version="1.0.0",
              contact={
                    "name": "Felipe Quinones",
                    "url": "https://www.utpl.edu.ec/",
                    "email": "fdquinones@utpl.edu.ec"
              },
              openapi_tags=tags_metadata
              )


# Lista vacía para almacenar los artículos creados.
ordenes = []


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

# Ruta para la página de inicio que devuelve un mensaje de bienvenida.


@app.get('/')
def bienvenida():
    return {'mensaje': 'Welcome a mi aplicación FastAPI Utpl 2028'}

# Ruta para obtener todos los artículos almacenados en la lista.
# El parámetro "response_model" especifica que la respuesta será una lista de objetos "Orden".


@app.get("/ordenes", response_model=List[Orden], tags=["ordenes"])
@version(2, 0)
async def leer_ordenes(session: Session = Depends(get_session), Verification=Depends(verification)):
    resultItems = session.exec(select(Orden)).all()
    return resultItems

# Ruta para crear un nuevo artículo.
# El parámetro "response_model" especifica que la respuesta será un objeto "Orden".
# ES


@app.post("/ordenes", response_model=Orden, tags=["ordenes"])
@version(2, 0)
async def crear_orden(orden: Orden, session: Session = Depends(get_session), Verification=Depends(verification)):
    session.add(orden)
    session.commit()
    session.refresh(orden)

    await send_message_telegram(f"Se ha creado una nueva orden con el id: {orden.id} y precio: {orden.precio} de nombre: {orden.producto}")
    send_email("Confirmación de orden", f"Se ha creado una nueva orden con el id: {orden.id} y precio: {orden.precio} de nombre: {orden.producto}", [
               "fdquinones@utpl.edu.ec"])
    return orden

# Ruta para actualizar una orden existente por su ID.
# El parámetro "response_model" especifica que la respuesta será un objeto "Orden".


@ app.put("/ordenes/{orden_id}", response_model=Orden, tags=["ordenes"])
async def actualizar_orden(orden_id: int, orden: OrdenActualizacion, session: Session = Depends(get_session), Verification=Depends(verification)):
    itemDB = session.get(Orden, orden_id)
    if itemDB is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if orden.precio is not None:
        itemDB.precio = orden.precio
    if orden.cantidad is not None:
        itemDB.cantidad = orden.cantidad
    session.add(itemDB)
    session.commit()
    session.refresh(itemDB)
    return orden

# Ruta para eliminar una orden por su ID.
# No se especifica "response_model" ya que no se devuelve ningún objeto en la respuesta.
# Este metodo elimina una orden por su ID.


@ app.delete("/ordenes/{orden_id}", tags=["ordenes"])
async def eliminar_orden(orden_id: int, session: Session = Depends(get_session), Verification=Depends(verification)):
    itemDB = session.get(Orden, orden_id)
    if itemDB is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    session.delete(itemDB)
    session.commit()

    return {"mensaje": "Orden eliminada"}  # Devuelve un mensaje informativo.


# Register new user using email, username, password
@ app.post("/register", response_model=GetUser, tags=["usuarios"])
@version(1, 0)
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


@ app.post("/login", tags=["usuarios"])
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

    token = create_access_token(user.id, timedelta(minutes=30))
    refresh = create_refresh_token(user.id, timedelta(minutes=1008))

    return {'access_token': token, 'token_type': 'bearer', 'refresh_token': refresh, "user_id": user.id}


@ app.get("/users/me", response_model=GetUser, tags=["usuarios"])
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user details
    """
    return current_user


app = VersionedFastAPI(app)
