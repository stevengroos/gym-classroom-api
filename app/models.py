from sqlalchemy import Column, Integer, String, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from app.database import Base

# Tabla intermedia para la relación Muchos a Muchos entre Entrenadores y Alumnos
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
    role = Column(String, nullable=False) # 'superadmin', 'trainer', 'student'
    full_name = Column(String, nullable=False)

    # Relación para entrenadores: Alumnos asociados
    students = relationship(
        "User",
        secondary=trainer_student_association,
        primaryjoin=id==trainer_student_association.c.trainer_id,
        secondaryjoin=id==trainer_student_association.c.student_id,
        backref="trainers"
    )

class Routine(Base):
    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False) # Ej: "Lunes - Pierna"
    day_of_week = Column(String, nullable=False) # Ej: "Lunes" o "Día 1"
    
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    exercises = relationship("Exercise", back_populates="routine", cascade="all, delete-orphan")

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    routine_id = Column(Integer, ForeignKey("routines.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    sets = Column(Integer, nullable=False)
    reps = Column(String, nullable=False) # String por si ponen "10-12" o "Al fallo" (Pensado en UX)
    rest_time = Column(String, nullable=True) # Ej: "90 segundos"
    youtube_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    routine = relationship("Routine", back_populates="exercises")