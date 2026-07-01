from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.dependencies import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse
from app.dependencies import get_current_trainer, get_current_superadmin
from app.security import get_password_hash

router = APIRouter(prefix="/users", tags=["Users"])

# Endpoint para el Entrenador: Crear un alumno y asociarlo a sí mismo
@router.post("/students", response_model=UserResponse)
def create_student(
    user_in: UserCreate, 
    db: Session = Depends(get_db), 
    current_trainer: User = Depends(get_current_trainer)
):
    # Verificar que el email no exista
    user_exists = db.query(User).filter(User.email == user_in.email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="El email ya está registrado.")
    
    # Forzar el rol a 'student' por seguridad, sin importar lo que envíe el frontend
    new_student = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role="student"
    )
    
    # Añadir a la base de datos
    db.add(new_student)
    
    # Magia de SQLAlchemy: Asociar el alumno al entrenador automáticamente
    current_trainer.students.append(new_student)
    
    db.commit()
    db.refresh(new_student)
    return new_student

# Endpoint para el Entrenador: Ver su lista de alumnos
@router.get("/my-students", response_model=List[UserResponse])
def get_my_students(db: Session = Depends(get_db), current_trainer: User = Depends(get_current_trainer)):
    # Gracias a la relación que definimos en models.py, esto devuelve solo sus alumnos
    return current_trainer.students

# Endpoint para el Superadmin: Crear un nuevo entrenador
@router.post("/trainers", response_model=UserResponse)
def create_trainer(
    user_in: UserCreate, 
    db: Session = Depends(get_db), 
    current_admin: User = Depends(get_current_superadmin)
):
    user_exists = db.query(User).filter(User.email == user_in.email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="El email ya está registrado.")
        
    new_trainer = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role="trainer"
    )
    db.add(new_trainer)
    db.commit()
    db.refresh(new_trainer)
    return new_trainer