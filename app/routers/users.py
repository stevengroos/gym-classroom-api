from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from app.dependencies import get_db
from app.models import User, Payment, Routine
from app.schemas import UserCreate, UserResponse, PaymentCreate, StudentUpdate, PaymentResponse, PasswordUpdate
from app.dependencies import get_current_trainer, get_current_superadmin, get_current_user
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
        phone=user_in.phone,
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

# ==========================================
# NUEVO: Endpoint para registrar mensualidades
# ==========================================
@router.post("/students/{student_id}/pay")
def register_payment(
    student_id: int,
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_trainer: User = Depends(get_current_trainer)
):
    # 1. Buscamos al alumno
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

    # 2. Registramos el pago en el historial
    new_payment = Payment(
        student_id=student.id,
        trainer_id=current_trainer.id,
        amount=payment_in.amount,
        notes=payment_in.notes
    )
    db.add(new_payment)

    # 3. Calculamos la nueva fecha de vencimiento
    now = datetime.now(timezone.utc)
    # Si no tiene fecha, o su fecha ya expiró en el pasado, partimos contando desde HOY
    if not student.expiration_date or student.expiration_date < now:
        base_date = now
    else:
        # Si pagó por adelantado, le sumamos los meses a la fecha que ya tenía
        base_date = student.expiration_date

    student.expiration_date = base_date + relativedelta(months=payment_in.add_months)
    student.default_price = payment_in.amount # Actualiza cuánto suele pagar este alumno

    db.commit()
    return {"message": "Pago registrado con éxito", "new_expiration": student.expiration_date}

# NUEVO: Activar / Inactivar Alumno
@router.put("/students/{student_id}/toggle-active")
def toggle_student_status(
    student_id: int,
    db: Session = Depends(get_db),
    current_trainer: User = Depends(get_current_trainer)
):
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    
    student.is_active = not student.is_active # Invierte el estado actual
    db.commit()
    return {"message": "Estado actualizado", "is_active": student.is_active}

# 1. Obtener el historial completo de pagos de un alumno específico
@router.get("/students/{student_id}/payments", response_model=List[PaymentResponse])
def get_student_payments(
    student_id: int,
    db: Session = Depends(get_db),
    current_trainer: User = Depends(get_current_trainer)
):
    payments = db.query(Payment).filter(
        Payment.student_id == student_id,
        Payment.trainer_id == current_trainer.id
    ).order_by(Payment.payment_date.desc()).all()
    return payments

# 2. Modificación Manual Avanzada del alumno (Fechas, Precios, Estados)
@router.put("/students/{student_id}/manage")
def manage_student(
    student_id: int,
    student_in: StudentUpdate,
    db: Session = Depends(get_db),
    current_trainer: User = Depends(get_current_trainer)
):
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
        
    if student_in.is_active is not None:
        student.is_active = student_in.is_active
    if student_in.expiration_date is not None:
        student.expiration_date = student_in.expiration_date
    if student_in.default_price is not None:
        student.default_price = student_in.default_price
    if student_in.phone is not None:       # <-- NUEVO
        student.phone = student_in.phone   # <-- NUEVO
        
    db.commit()
    db.refresh(student)
    return student

# 3. Endpoint para que el Alumno vea su propio perfil y estado de pago
@router.get("/me/profile", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user

# 1. Cambiar la contraseña de un alumno (Entrenador)
@router.put("/students/{student_id}/password")
def update_student_password(
    student_id: int,
    pass_in: PasswordUpdate,
    db: Session = Depends(get_db),
    current_trainer: User = Depends(get_current_trainer)
):
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
        
    student.hashed_password = get_password_hash(pass_in.new_password)
    db.commit()
    return {"message": "Contraseña del alumno actualizada con éxito"}

# 2. Cambiar mi propia contraseña (Entrenador/Alumno)
@router.put("/me/password")
def update_my_password(
    pass_in: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Sirve para cualquier rol
):
    current_user.hashed_password = get_password_hash(pass_in.new_password)
    db.commit()
    return {"message": "Tu contraseña ha sido actualizada"}

# ==========================================
# RUTAS EXCLUSIVAS PARA EL SUPERADMIN
# ==========================================

@router.get("/trainers")
def get_all_trainers(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="No tienes permisos de SuperAdmin")
    
    trainers = db.query(User).filter(User.role == "trainer").order_by(User.id.desc()).all()
    
    result = []
    for t in trainers:
        student_count = len(t.students)
        result.append({
            "id": t.id,
            "full_name": t.full_name,
            "email": t.email,
            "is_active": t.is_active,
            "student_count": student_count,
            "created_at": t.created_at,
            "expiration_date": t.expiration_date
        })
    return result

@router.get("/trainers/{trainer_id}/details")
def get_trainer_details(trainer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="No tienes permisos")
        
    trainer = db.query(User).filter(User.id == trainer_id, User.role == "trainer").first()
    if not trainer:
        raise HTTPException(status_code=404, detail="Entrenador no encontrado")
    
    routines = db.query(Routine).filter(Routine.trainer_id == trainer_id).all()
    
    return {
        "students": [{"id": s.id, "full_name": s.full_name, "email": s.email, "is_active": s.is_active} for s in trainer.students],
        "routines": [{"id": r.id, "title": r.title, "day_of_week": r.day_of_week, "is_template": r.is_template} for r in routines]
    }

@router.put("/trainers/{trainer_id}/toggle")
def toggle_trainer_status(trainer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="No tienes permisos")
        
    trainer = db.query(User).filter(User.id == trainer_id, User.role == "trainer").first()
    if not trainer:
        raise HTTPException(status_code=404, detail="Entrenador no encontrado")
    
    trainer.is_active = not trainer.is_active
    db.commit()
    return {"message": "Estado del entrenador actualizado", "is_active": trainer.is_active}

@router.post("/trainers/{trainer_id}/pay")
def pay_trainer_subscription(trainer_id: int, payment_in: PaymentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="No tienes permisos")
        
    trainer = db.query(User).filter(User.id == trainer_id, User.role == "trainer").first()
    if not trainer:
        raise HTTPException(status_code=404, detail="Entrenador no encontrado")
    
    # 1. NUEVO: Guardamos físicamente el registro de pago en el historial global usando tu tabla de pagos
    # Usamos el id del superadmin en trainer_id o un ID fijo si prefieres, pero registrarlo con el student_id apuntando al entrenador es lo ideal para reutilizar el modelo
    new_payment = Payment(
        student_id=trainer.id, # El cliente aquí es el entrenador
        trainer_id=current_user.id, # El cobrador es el superadmin
        amount=payment_in.amount,
        notes=payment_in.notes or "Renovación de Licencia SaaS"
    )
    db.add(new_payment)

    # 2. Actualizamos su vigencia
    now = datetime.now(timezone.utc)
    if not trainer.expiration_date or trainer.expiration_date < now:
        base_date = now
    else:
        base_date = trainer.expiration_date

    trainer.expiration_date = base_date + relativedelta(months=payment_in.add_months)
    db.commit()
    return {"message": "Suscripción renovada con éxito", "new_expiration": trainer.expiration_date}

# NUEVO ENDPOINT: Obtener el historial de pagos de un entrenador específico
@router.get("/trainers/{trainer_id}/payments", response_model=List[PaymentResponse])
def get_trainer_payments(
    trainer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="No tienes permisos")
        
    payments = db.query(Payment).filter(
        Payment.student_id == trainer_id,
        Payment.trainer_id == current_user.id
    ).order_by(Payment.payment_date.desc()).all()
    return payments