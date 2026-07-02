from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Esquemas de Usuario ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str # "student" o "trainer"

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    # NUEVO: Datos financieros que el frontend necesita mostrar
    expiration_date: Optional[datetime] = None
    default_price: Optional[float] = None
    is_active: Optional[bool] = True # <-- NUEVO

    class Config:
        from_attributes = True

# --- NUEVO: Esquemas de Pagos ---
class PaymentCreate(BaseModel):
    amount: float
    notes: Optional[str] = None
    add_months: int = 1 # Por defecto suma 1 mes al vencimiento

class PaymentResponse(BaseModel):
    id: int
    amount: float
    payment_date: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True

# --- Esquemas de Ejercicios y Rutinas ---
class ExerciseBase(BaseModel):
    name: str
    sets: int
    reps: str
    rest_time: Optional[str] = None
    youtube_url: Optional[str] = None
    notes: Optional[str] = None

class RoutineCreate(BaseModel):
    title: str
    day_of_week: str
    # NUEVO: student_id ahora es opcional (para poder crear plantillas huérfanas)
    student_id: Optional[int] = None
    is_template: Optional[bool] = False 
    exercises: List[ExerciseBase]

class RoutineResponse(BaseModel):
    id: int
    title: str
    day_of_week: str
    is_template: bool
    exercises: List[ExerciseBase]

    class Config:
        from_attributes = True
        
# --- Esquemas de Registro de Entrenamiento ---
class WorkoutLogCreate(BaseModel):
    feedback: Optional[str] = None
    weights: Optional[Dict[str, Any]] = None
    
class StudentUpdate(BaseModel):
    is_active: Optional[bool] = None
    expiration_date: Optional[datetime] = None
    default_price: Optional[float] = None
    
# Esquema para actualizar contraseñas
class PasswordUpdate(BaseModel):
    new_password: str
    
    
# --- NUEVO: Esquema para el Dashboard del SuperAdmin ---
class TrainerDashboardResponse(BaseModel):
    id: int
    full_name: str
    email: str
    is_active: bool
    student_count: int
    created_at: datetime

    class Config:
        from_attributes = True