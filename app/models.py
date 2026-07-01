from sqlalchemy import Column, Integer, String, ForeignKey, Table, Text, DateTime, JSON, Boolean, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

# Tabla intermedia Entrenador-Alumno
trainer_student_association = Table(
    'trainer_student',
    Base.metadata,
    Column('trainer_id', Integer, ForeignKey('users.id', ondelete="CASCADE")),
    Column('student_id', Integer, ForeignKey('users.id', ondelete="CASCADE"))
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    
    # NUEVO: Gestión de Mensualidades
    expiration_date = Column(DateTime(timezone=True), nullable=True) # Cuándo se le vence el gym
    default_price = Column(Float, nullable=True, default=0.0) # Lo que suele pagar este alumno
    is_active = Column(Boolean, default=True) # <-- NUEVO

    students = relationship(
        "User",
        secondary=trainer_student_association,
        primaryjoin=id==trainer_student_association.c.trainer_id,
        secondaryjoin=id==trainer_student_association.c.student_id,
        backref="trainers"
    )

# NUEVA TABLA: Registro Histórico de Pagos
class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    amount = Column(Float, nullable=False) # Cuánto pagó
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(String, nullable=True) # Ej: "Pagó en efectivo la mitad, debe 10"
    
    student = relationship("User", foreign_keys=[student_id])
    trainer = relationship("User", foreign_keys=[trainer_id])

class Routine(Base):
    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False) 
    day_of_week = Column(String, nullable=False) 
    
    # NUEVO: Para saber si es una rutina real o una plantilla base clonable
    is_template = Column(Boolean, default=False) 
    
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True) # Nullable para plantillas generales
    trainer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    exercises = relationship("Exercise", back_populates="routine", cascade="all, delete-orphan")

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    routine_id = Column(Integer, ForeignKey("routines.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    sets = Column(Integer, nullable=False)
    reps = Column(String, nullable=False) 
    rest_time = Column(String, nullable=True) 
    youtube_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    routine = relationship("Routine", back_populates="exercises")

class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    routine_id = Column(Integer, ForeignKey("routines.id", ondelete="CASCADE"), nullable=False)
    
    completed_at = Column(DateTime(timezone=True), server_default=func.now()) 
    
    feedback = Column(Text, nullable=True)
    weights_data = Column(JSON, nullable=True) 

    student = relationship("User", backref="workout_logs", foreign_keys=[student_id])
    routine = relationship("Routine", backref="logs")