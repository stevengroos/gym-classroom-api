from app.database import SessionLocal, engine, Base
from app.models import User
from app.security import get_password_hash

# Asegurarnos de que las tablas existan
Base.metadata.create_all(bind=engine)

def create_superadmin():
    db = SessionLocal()
    email = "admin@gymclassroom.com"
    
    # Comprobar si ya existe
    admin = db.query(User).filter(User.email == email).first()
    if admin:
        print("El Superadmin ya existe.")
        return

    # Crear al superadmin
    superadmin = User(
        email=email,
        hashed_password=get_password_hash("TuPasswordSuperSeguro123!"),
        full_name="Super Administrador",
        role="superadmin"
    )
    
    db.add(superadmin)
    db.commit()
    print(f"Superadmin creado con éxito. Email: {email}")
    db.close()

if __name__ == "__main__":
    create_superadmin()