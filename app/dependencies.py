from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.models import User

# Le dice a FastAPI de dónde sacar el token en las peticiones
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == user_email).first()
    if user is None:
        raise credentials_exception
    return user

# Guardianes de Roles
def get_current_trainer(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["trainer", "superadmin"]:
        raise HTTPException(status_code=403, detail="Privilegios insuficientes. Se requiere rol de entrenador.")
    return current_user

def get_current_superadmin(current_user: User = Depends(get_current_user)):
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo superadmin.")
    return current_user