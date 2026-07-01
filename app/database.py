from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from sqlalchemy.ext.declarative import declarative_base

# Conexión directa desde la configuración (.env)
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Agrega pool_pre_ping=True aquí:
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    pool_pre_ping=True  # <--- ESTA ES LA MAGIA
)

# Engine de SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Creador de sesiones para interactuar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para crear los modelos (la usamos en models.py)
Base = declarative_base()