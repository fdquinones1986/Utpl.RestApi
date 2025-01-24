from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlmodel import Session, select
from app.models import User  # Importa desde el módulo models dentro del paquete app
from app.db import engine  # Asegúrate de tener un motor de base de datos configurado
from jose import jwt, JWTError
from app.config import Settings

# Configuración de JWT y seguridad
SECRET_KEY = "m4vwKInT"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Función para hashear contraseñas
def secure_pwd(raw_password: str) -> str:
    return pwd_context.hash(raw_password)


# Función para verificar contraseñas
def verify_pwd(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Función para autenticar usuarios
def authenticate_user(session: Session, email: str, password: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    result = session.exec(statement).first()
    if result and verify_pwd(password, result.hashed_password):
        return result
    return None


# Función para generar un token de acceso
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Función para decodificar y validar un token JWT
def decodeJWT(token: str):
    try:
        payload = jwt.decode(token, Settings.SECRET_KEY, algorithms=[Settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )



# Dependencia para obtener el usuario actual basado en el token
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = decodeJWT(token)
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user


# Dependencia para validar usuarios con roles específicos (opcional)
def get_current_user_with_role(required_role: str, token: str = Depends(oauth2_scheme)) -> User:
    user = get_current_user(token)
    if user.role != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tienes permisos de {required_role}.",
        )
    return user


# Función para obtener un usuario por su correo electrónico
def get_user_by_email(db: Session, email: str):
    """
    Busca un usuario por su correo electrónico en la base de datos.
    """
    return db.query(User).filter(User.email == email).first()


# Función para crear un nuevo usuario
def create_user(db: Session, email: str, password: str, role: str = "user") -> User:
    """
    Crea un nuevo usuario en la base de datos.
    
    Args:
        db (Session): Sesión de la base de datos.
        email (str): Correo electrónico del usuario.
        password (str): Contraseña del usuario.
        role (str): Rol del usuario (opcional, valor por defecto: "user").
    
    Returns:
        User: El usuario recién creado.
    """
    # Verificar si ya existe un usuario con el mismo correo
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya está registrado.",
        )
    
    # Crear el hash de la contraseña
    hashed_password = secure_pwd(password)

    # Crear el nuevo usuario
    new_user = User(email=email, hashed_password=hashed_password, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Actualiza el objeto con datos de la base de datos
    return new_user

