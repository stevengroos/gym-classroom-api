from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.dependencies import get_db
from app.models import User, Routine, Exercise, WorkoutLog
from app.schemas import RoutineCreate, RoutineResponse, WorkoutLogCreate
from app.dependencies import get_current_user, get_current_trainer


router = APIRouter(prefix="/routines", tags=["Routines"])

# Endpoint para el Alumno: Ver SUS rutinas
@router.get("/me", response_model=List[RoutineResponse])
def get_my_routines(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # El filtro por student_id garantiza que solo vea lo suyo
    routines = db.query(Routine).filter(Routine.student_id == current_user.id).all()
    return routines

# Endpoint para el Entrenador: Crear una rutina para un alumno o una PLANTILLA
@router.post("/", response_model=RoutineResponse)
def create_routine(
    routine_in: RoutineCreate, 
    db: Session = Depends(get_db), 
    current_trainer: User = Depends(get_current_trainer)
):
    new_routine = Routine(
        title=routine_in.title,
        day_of_week=routine_in.day_of_week,
        student_id=routine_in.student_id, # Puede ser None si es plantilla
        trainer_id=current_trainer.id,
        is_template=routine_in.is_template # NUEVO: Guardamos si es plantilla
    )
    db.add(new_routine)
    db.commit()
    db.refresh(new_routine)

    # Guardar los ejercicios asociados
    for exercise in routine_in.exercises:
        new_exercise = Exercise(
            routine_id=new_routine.id,
            **exercise.model_dump()
        )
        db.add(new_exercise)
    
    db.commit()
    db.refresh(new_routine)
    return new_routine

# 1. Endpoint para que el Entrenador vea las rutinas de un alumno específico
@router.get("/student/{student_id}", response_model=List[RoutineResponse])
def get_student_routines(
    student_id: int, 
    db: Session = Depends(get_db), 
    current_trainer: User = Depends(get_current_trainer)
):
    # Por seguridad (ISO 27001), verificamos que la rutina pertenezca a un alumno de este entrenador
    routines = db.query(Routine).filter(
        Routine.student_id == student_id,
        Routine.trainer_id == current_trainer.id
    ).all()
    return routines

# 2. Endpoint para que el Entrenador EDITE una rutina existente
@router.put("/{routine_id}", response_model=RoutineResponse)
def update_routine(
    routine_id: int,
    routine_in: RoutineCreate,
    db: Session = Depends(get_db),
    current_trainer: User = Depends(get_current_trainer)
):
    # 1. Buscar la rutina existente
    db_routine = db.query(Routine).filter(
        Routine.id == routine_id, 
        Routine.trainer_id == current_trainer.id
    ).first()
    
    if not db_routine:
        raise HTTPException(status_code=404, detail="Rutina no encontrada o no tienes permisos.")

    # 2. Actualizar los datos básicos de la cabecera
    db_routine.title = routine_in.title
    db_routine.day_of_week = routine_in.day_of_week
    
    # 3. Borrar los ejercicios anteriores para evitar duplicados o desorden (UX Limpio)
    db.query(Exercise).filter(Exercise.routine_id == routine_id).delete()

    # 4. Insertar los nuevos ejercicios modificados
    for exercise in routine_in.exercises:
        new_exercise = Exercise(
            routine_id=db_routine.id,
            **exercise.model_dump()
        )
        db.add(new_exercise)

    db.commit()
    db.refresh(db_routine)
    return db_routine


# 3. Endpoint para que el Alumno guarde su entrenamiento completado
@router.post("/{routine_id}/log")
def log_workout(
    routine_id: int,
    log_in: WorkoutLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Obtenemos al alumno logueado
):
    # Validamos que la rutina exista y pertenezca a este alumno
    routine = db.query(Routine).filter(
        Routine.id == routine_id, 
        Routine.student_id == current_user.id
    ).first()
    
    if not routine:
        raise HTTPException(status_code=404, detail="Rutina no encontrada.")

    # Creamos el registro histórico
    new_log = WorkoutLog(
        student_id=current_user.id,
        routine_id=routine_id,
        feedback=log_in.feedback,
        weights_data=log_in.weights
    )
    
    db.add(new_log)
    db.commit()
    
    return {"message": "¡Entrenamiento guardado con éxito!"}

# 4. Endpoint para que el Entrenador vea el HISTORIAL de entrenamientos de un alumno
@router.get("/student/{student_id}/logs")
def get_student_workout_logs(
    student_id: int,
    db: Session = Depends(get_db),
    current_trainer: User = Depends(get_current_trainer)
):
    # Buscamos los logs del alumno, ordenados desde el más reciente al más viejo
    logs = db.query(WorkoutLog).filter(
        WorkoutLog.student_id == student_id
    ).order_by(WorkoutLog.completed_at.desc()).all()
    
    # Formateamos una respuesta limpia para el frontend
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "completed_at": log.completed_at.strftime("%d/%m/%Y %H:%M") if log.completed_at else "Sin fecha",
            "feedback": log.feedback,
            "weights_data": log.weights_data,
            "routine_title": log.routine.title if log.routine else "Rutina eliminada",
            # Pasamos los nombres de los ejercicios para que el entrenador sepa a qué corresponde cada peso
            "exercises": [{"name": ex.name, "index": idx} for idx, ex in enumerate(log.routine.exercises)] if log.routine else []
        })
        
    return result

# 5. Endpoint para obtener las Plantillas del Entrenador
@router.get("/trainer/templates", response_model=List[RoutineResponse])
def get_routine_templates(
    db: Session = Depends(get_db),
    current_trainer: User = Depends(get_current_trainer)
):
    # Buscamos todas las rutinas de este entrenador marcadas como plantilla
    templates = db.query(Routine).filter(
        Routine.trainer_id == current_trainer.id,
        Routine.is_template == True
    ).all()
    return templates

# NUEVO: Eliminar una Rutina o Plantilla
@router.delete("/{routine_id}")
def delete_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    current_trainer: User = Depends(get_current_trainer)
):
    routine = db.query(Routine).filter(
        Routine.id == routine_id, 
        Routine.trainer_id == current_trainer.id
    ).first()
    
    if not routine:
        raise HTTPException(status_code=404, detail="Rutina no encontrada o sin permisos")
        
    db.delete(routine)
    db.commit()
    return {"message": "Eliminada con éxito"}

# 6. Endpoint para obtener el último registro de una rutina específica (Historial Inmediato)
@router.get("/{routine_id}/last-log")
def get_last_routine_log(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    last_log = db.query(WorkoutLog).filter(
        WorkoutLog.routine_id == routine_id,
        WorkoutLog.student_id == current_user.id
    ).order_by(WorkoutLog.completed_at.desc()).first()
    
    if last_log and last_log.weights_data:
        return {"weights_data": last_log.weights_data}
    return {"weights_data": {}}