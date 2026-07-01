from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.dependencies import get_db
from app.models import User, Routine, Exercise
from app.schemas import RoutineCreate, RoutineResponse
from app.dependencies import get_current_user, get_current_trainer

router = APIRouter(prefix="/routines", tags=["Routines"])

# Endpoint para el Alumno: Ver SUS rutinas
@router.get("/me", response_model=List[RoutineResponse])
def get_my_routines(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # El filtro por student_id garantiza que solo vea lo suyo
    routines = db.query(Routine).filter(Routine.student_id == current_user.id).all()
    return routines

# Endpoint para el Entrenador: Crear una rutina para un alumno
@router.post("/", response_model=RoutineResponse)
def create_routine(
    routine_in: RoutineCreate, 
    db: Session = Depends(get_db), 
    current_trainer: User = Depends(get_current_trainer)
):
    # Opcional: Aquí podrías verificar si routine_in.student_id realmente pertenece a este current_trainer
    
    new_routine = Routine(
        title=routine_in.title,
        day_of_week=routine_in.day_of_week,
        student_id=routine_in.student_id,
        trainer_id=current_trainer.id # Registramos automáticamente quién la creó
    )
    db.add(new_routine)
    db.commit()
    db.refresh(new_routine)

    # Guardar los ejercicios asociados a esta rutina
    for exercise in routine_in.exercises:
        new_exercise = Exercise(
            routine_id=new_routine.id,
            **exercise.model_dump()
        )
        db.add(new_exercise)
    
    db.commit()
    db.refresh(new_routine)
    return new_routine