from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth
from app.routers import routines, users  # <-- ¡Línea descomentada!

# Crea las tablas en la base de datos (PostgreSQL/Supabase) al iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Gym Classroom API",
    description="API para gestión de entrenamientos personalizados",
    version="1.0.0"
)

# Configuración CORS para permitir peticiones desde tu frontend en Reactttt
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción cambiar por la URL de Vercel (ej. ["https://tu-app.vercel.app"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir las rutas (¡Líneas descomentadas!)
app.include_router(auth.router)
app.include_router(routines.router)
app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "Bienvenido a la API de Gym Classroom"}