from typing import Optional, List, Tuple
from sqlmodel import Session, select
from datetime import datetime
from .models import User, Patient, PatientCreate, PatientUpdate


def create_user(session: Session, username: str, hashed_password: str) -> User:
    user = User(username=username, hashed_password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user_by_username(session: Session, username: str) -> Optional[User]:
    statement = select(User).where(User.username == username)
    return session.exec(statement).first()


def create_patient(session: Session, patient_in: PatientCreate) -> Patient:
    patient = Patient.model_validate(patient_in)
    session.add(patient)
    session.commit()
    session.refresh(patient)
    return patient


def get_patient(session: Session, patient_id: int) -> Optional[Patient]:
    return session.get(Patient, patient_id)


def update_patient(
        session: Session,
        patient_id: int,
        patient_update: PatientUpdate
) -> Optional[Patient]:
    patient = session.get(Patient, patient_id)
    if not patient:
        return None

    update_data = patient_update.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        for field, value in update_data.items():
            setattr(patient, field, value)
        session.commit()
        session.refresh(patient)

    return patient


def delete_patient(session: Session, patient_id: int) -> bool:
    patient = session.get(Patient, patient_id)
    if not patient:
        return False

    session.delete(patient)
    session.commit()
    return True


def list_patients(
    session: Session,
    *,
    name: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    symptom: Optional[str] = None,
    offset: int = 0,
    limit: int = 100
) -> Tuple[List[Patient], int]:
    """
    Listado de pacientes con filtros y paginación.
    Retorna una tupla de (pacientes, conteo_total)
    """
    # Construir query base
    q = select(Patient)

    # Aplicar filtros
    if name:
        q = q.where(Patient.name.ilike(f"%{name}%"))
    if min_age is not None:
        q = q.where(Patient.age >= min_age)
    if max_age is not None:
        q = q.where(Patient.age <= max_age)
    if symptom:
        q = q.where(Patient.symptoms.like(f"%{symptom}%"))

    # Obtener total para paginación
    count_query = select(Patient)
    if name:
        count_query = count_query.where(Patient.name.ilike(f"%{name}%"))
    if min_age is not None:
        count_query = count_query.where(Patient.age >= min_age)
    if max_age is not None:
        count_query = count_query.where(Patient.age <= max_age)
    if symptom:
        count_query = count_query.where(Patient.symptoms.like(f"%{symptom}%"))

    total_count = len(session.exec(count_query).all())

    # Aplicar paginación
    q = q.offset(offset).limit(limit)

    # Ordenar por fecha de creación descendente
    q = q.order_by(Patient.created_at.desc())

    patients = session.exec(q).all()
    return patients, total_count


def get_patients_by_symptom(session: Session, symptom: str) -> List[Patient]:
    """Obtener todos los pacientes que tienen un síntoma específico"""
    statement = select(Patient).where(Patient.symptoms.like(f"%{symptom}%"))
    return session.exec(statement).all()


def get_patients_by_age_range(
        session: Session,
        min_age: int,
        max_age: int
) -> List[Patient]:
    """Obtener todos los pacientes dentro de un rango de edad"""
    statement = select(Patient).where(
        Patient.age >= min_age,
        Patient.age <= max_age
    )
    return session.exec(statement).all()
