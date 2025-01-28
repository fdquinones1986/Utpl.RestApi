from sqlmodel import Session, select
from app.models import PostUser, User, Token
from pydantic import EmailStr
from datetime import date, datetime, timedelta, time 

from typing import Union, Any, Optional

from app.utils.passwords import secure_pwd

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


from fastapi import Depends, HTTPException, status, Request

from app.config import Settings

from jose import jwt, JWTError


#  Funcion 
def get_user(db: Session, email: EmailStr):
    return db.query(User).filter(User.email == email).first()


# Función para crear un nuevo usuario
def create_user(db: Session,  user: PostUser, role: str = "user"):
    # Crear el hash de la contraseña
    passHash = secure_pwd(user.password)

    # Crear el nuevo usuario
    new_user = User(email=user.email, hashed_password=passHash, role=role, username=user.username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Actualiza el objeto con datos de la base de datos
    return new_user

# Función para obtener un usuario por su ID
def get_token(db: Session, token: str):
    return db.query(Token).filter(Token.token == token).first()

# Función para crear un nuevo token
def create_token(db: Session, token: str, user_id: int):
    db_token = Token(token=token, user_id=user_id)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token ("Token creado correctamente")

# Función para crear un nuevo token
def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=Settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, Settings.secret_key, Settings.algorithm)
    return encoded_jwt

# Función para crear un nuevo token de refresco
def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow(
        ) + timedelta(minutes=Settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, Settings.refresh_secret_key, Settings.algorithm)
    return encoded_jwt

# Función para decodificar un token
def decodeJWT(jwtoken: str):
    try:
        payload = jwt.decode(jwtoken, Settings.secret_key, Settings.algorithm)
        return payload
    except JWTError:
        return None

# Función para verificar si un token es válido
# Verificación jwt
class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            token = credentials.credentials
            if not self.verify_jwt(token):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return token
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:
        try:
            payload = decodeJWT(jwtoken)
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.JWTError:
            return False