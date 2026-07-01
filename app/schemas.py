from pydantic import BaseModel, EmailStr
from typing import List, Optional

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
    student_id: int
    exercises: List[ExerciseBase]

class RoutineResponse(BaseModel):
    id: int
    title: str
    day_of_week: str
    exercises: List[ExerciseBase]

    class Config:
        from_attributes = True