from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

# Lista de usuarios con sus credenciales y token de autenticación.
users = {
    "admin": {
        "password": "Passw0rd123",
        "token": "",
        "priviliged": True
    }
}

# Función para autenticar a un usuario.


def verification(creds: HTTPBasicCredentials = Depends(security)):
    username = creds.username
    password = creds.password

    if username in users and password == users[username]["password"]:
        print('Usuario autenticado')
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
