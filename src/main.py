from fastapi import FastAPI, Depends, HTTPException, Query, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from typing import Optional
from sqlmodel import Session
from contextlib import asynccontextmanager

import logging
from .database import init_db, get_session, engine, check_db_connection
from .models import Patient, PatientCreate, PatientUpdate, User, UserCreate
from .crud import create_user, get_user_by_username, create_patient, \
    get_patient, list_patients, update_patient, delete_patient
from .auth import get_password_hash, authenticate_user, create_access_token, \
    get_current_user
from .settings import get_settings


# Obtener configuración
settings = get_settings()
DATABASE_URL = settings.database_url

# Crear routers para organizar endpoints
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
patients_router = APIRouter(prefix="/patients", tags=["Patients"])
health_router = APIRouter(tags=["Health"])


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()

    try:
        logger.info("LIFESPAN startup - DATABASE_URL=%s", DATABASE_URL)

        if not check_db_connection():
            message = "DB inicializada pero no accesible"
            logger.error(message)
            raise RuntimeError(message)

        yield
    except Exception:
        message = "Fallo en el initialization flow durante lifespan startup"
        logger.exception(message)
        raise
    finally:
        # Shutdown: dispose engine
        try:
            engine.dispose()
        except Exception:
            pass


# Crear la aplicación FastAPI
app = FastAPI(
    title="Patients API",
    version="1.0",
    description="API para gestión de pacientes",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware de seguridad (solo en producción)
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"]
    )


# Auth endpoints
@auth_router.post("/register", response_model=dict, status_code=201)
def register(user_in: UserCreate, session: Session = Depends(get_session)):
    username = user_in.username
    password = user_in.password

    # Validación de contraseña
    if len(password) < 8:
        message = "La contraseña debe tener al menos 8 caracteres"
        raise HTTPException(
            status_code=400,
            detail=message
        )

    existing = get_user_by_username(session, username)
    if existing:
        message = "El nombre de usuario ya existe"
        raise HTTPException(status_code=400, detail=message)

    user = create_user(
        session,
        username=username,
        hashed_password=get_password_hash(password)
    )
    return {"username": user.username, "id": user.id}


@auth_router.post("/login", response_model=dict)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        message = "Nombre de usuario o contraseña incorrectos"
        raise HTTPException(
            status_code=401,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# Patient endpoints (protected)
@patients_router.post("", response_model=Patient, status_code=201)
def endpoint_create_patient(
    patient_in: PatientCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    return create_patient(session, patient_in)


@patients_router.get("", response_model=dict)
def endpoint_list_patients(
    name: Optional[str] = Query(None, description="Filtrar por nombre"),
    min_age: Optional[int] = Query(None, ge=0, le=120, description="Edad mínima"),
    max_age: Optional[int] = Query(None, ge=0, le=120, description="Edad máxima"),
    symptom: Optional[str] = Query(None, description="Filrar por síntoma"),
    offset: int = Query(0, ge=0, description="Desplazamiento de paginación"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de paginación"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    patients, total_count = list_patients(
        session,
        name=name,
        min_age=min_age,
        max_age=max_age,
        symptom=symptom,
        offset=offset,
        limit=limit
    )
    return {
        "patients": patients,
        "total_count": total_count,
        "offset": offset,
        "limit": limit,
        "has_more": offset + limit < total_count
    }


@patients_router.get("/{patient_id}", response_model=Patient)
def endpoint_get_patient(
    patient_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    patient = get_patient(session, patient_id)
    if not patient:
        message = "Paciente no encontrado"
        raise HTTPException(status_code=404, detail=message)
    return patient


@patients_router.put("/{patient_id}", response_model=Patient)
def endpoint_update_patient(
    patient_id: int,
    patient_update: PatientUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    patient = update_patient(session, patient_id, patient_update)
    if not patient:
        message = "Paciente no encontrado"
        raise HTTPException(status_code=404, detail=message)
    return patient


@patients_router.delete("/{patient_id}", status_code=204)
def endpoint_delete_patient(
    patient_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    success = delete_patient(session, patient_id)
    if not success:
        message = "Paciente no encontrado"
        raise HTTPException(status_code=404, detail=message)


# Health check endpoint
@health_router.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0"}


app.include_router(auth_router, prefix="/api/v1")
app.include_router(patients_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
