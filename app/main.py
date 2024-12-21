from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Annotated

from app.models import Orden, OrdenActualizacion
from sqlmodel import Session, select
from app.db import init_db, get_session

from fastapi.security import HTTPBasic, HTTPBasicCredentials
security = HTTPBasic()

app = FastAPI()


# Lista vacía para almacenar los artículos creados.
ordenes = []


@app.on_event("startup")
def on_startup():
    init_db()

# Ruta para la página de inicio que devuelve un mensaje de bienvenida.


@app.get('/')
def bienvenida():
    return {'mensaje': 'Welcome a mi aplicación FastAPI Utpl 2028'}

# Ruta para obtener el usuario actual.


@app.get("/users/me")
def read_current_user(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    return {"username": credentials.username, "password": credentials.password}

# Ruta para obtener todos los artículos almacenados en la lista.
# El parámetro "response_model" especifica que la respuesta será una lista de objetos "Orden".


@app.get("/ordenes", response_model=List[Orden])
async def leer_ordenes(session: Session = Depends(get_session)):
    resultItems = session.exec(select(Orden)).all()
    return resultItems

# Ruta para crear un nuevo artículo.
# El parámetro "response_model" especifica que la respuesta será un objeto "Orden".
# ES


@app.post("/ordenes", response_model=Orden)
async def crear_orden(orden: Orden, session: Session = Depends(get_session)):
    session.add(orden)
    session.commit()
    session.refresh(orden)

    return orden

# Ruta para actualizar una orden existente por su ID.
# El parámetro "response_model" especifica que la respuesta será un objeto "Orden".


@app.put("/ordenes/{orden_id}", response_model=Orden)
async def actualizar_orden(orden_id: int, orden: OrdenActualizacion, session: Session = Depends(get_session)):
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


@app.delete("/ordenes/{orden_id}")
async def eliminar_orden(orden_id: int, session: Session = Depends(get_session)):
    itemDB = session.get(Orden, orden_id)
    if itemDB is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    session.delete(itemDB)
    session.commit()

    return {"mensaje": "Orden eliminada"}  # Devuelve un mensaje informativo.
