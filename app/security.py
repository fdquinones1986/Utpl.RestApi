from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

# Usuarios con credenciales y token.
users = {
    "admin": {
        "password": "ContraseñaSegura123",
        "token": "",
        "priviliged": True
    }
}

# Autenticar usuario.

def verification(creds: HTTPBasicCredentials = Depends(security)):
    username = creds.username
    password = creds.password

    if username in users and password == users[username]["password"]:
        print('Usuario verificado y autenticado')
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales no correctas",
            headers={"WWW-Authenticate": "Basic"},
        )