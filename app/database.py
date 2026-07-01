from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Conexión directa desde la configuración (.env)
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Engine de SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Creador de sesiones para interactuar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para crear los modelos (la usamos en models.py)
Base = declarative_base()