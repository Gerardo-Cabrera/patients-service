from typing import Optional, List, Annotated
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
from pydantic import field_validator, StringConstraints


class PatientBase(SQLModel):
    name: Annotated[str, StringConstraints(
        min_length=1,
        max_length=100)
    ] = Field(
        ...,
        description="Nombre completo del paciente"
    )
    age: int = Field(
        ..., ge=0,
        le=120,
        description="Edad entre 0 y 120 años"
    )
    symptoms: Optional[List[str]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Listado de síntomas del paciente"
    )

    @field_validator('name')
    def validate_name(cls, v):
        if not v.strip():
            message = "No puede estar vacío"
            raise ValueError(message)
        return v.strip()

    @field_validator('symptoms')
    def validate_symptoms(cls, v):
        if v is None:
            return []
        return [symptom.strip() for symptom in v if symptom.strip()]


class Patient(PatientBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Hora de creación del registro"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Hora de la última actualización del registro"
    )


class PatientCreate(PatientBase):
    pass


class PatientUpdate(SQLModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    symptoms: Optional[List[str]] = None


class UserBase(SQLModel):
    username: Annotated[str, StringConstraints(
        min_length=3,
        max_length=50)
    ] = Field(
        ...,
        description="Nombre de usuario para autenticación"
    )


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(
        ...,
        description="Hashed password usando bcrypt"
    )
    is_active: bool = Field(
        default=True,
        description="Verifica si la cuenta de usuario está activa"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Hora de creación del usuario"
    )


class UserCreate(UserBase):
    username: str = Field(..., min_length=3, description="Username")
    password: Annotated[str, StringConstraints(min_length=8)] = Field(
        ...,
        description="Mínimo 8 caracteres"
    )
