import pytest
from fastapi.testclient import TestClient

import src.main as app_main
from src.database import init_db, engine
from src.settings import get_settings
from sqlmodel import SQLModel


# Inicializar DB en memoria para tests
settings = get_settings()
if settings.database_url != "sqlite:///:memory:":
    message = "Tests deben usar base de datos SQLite en memoria"
    raise RuntimeError(message)
init_db()


@pytest.fixture(autouse=True)
def setup_db():
    # Crear tablas antes de cada test
    SQLModel.metadata.create_all(engine)
    yield
    # Opcional: limpiar datos después de cada test
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def client():
    client = TestClient(app_main.app)
    yield client


@pytest.fixture
def auth_headers(client):
    # Registrar y loguear un usuario para obtener token
    client.post(
        "/api/v1/auth/register",
        json={
            "username":"testuser",
            "password":"testpass123"
        }
    )
    r = client.post(
        "/api/v1/auth/login",
        data={
            "username":"testuser",
            "password":"testpass123"
        }
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_login_and_patient_flow(client, auth_headers):
    # Crear paciente
    patient_payload = {"name":"Bob","age":40,"symptoms":["fever","cough"]}
    r = client.post(
        "/api/v1/patients",
        json=patient_payload,
        headers=auth_headers
    )
    assert r.status_code == 201
    created = r.json()
    assert created["name"] == "Bob"
    assert created["age"] == 40
    assert created["symptoms"] == ["fever", "cough"]

    # Listar pacientes
    r = client.get("/api/v1/patients", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "patients" in data
    assert "total_count" in data
    assert len(data["patients"]) >= 1

    # Obtener paciente por ID
    pid = created["id"]
    r = client.get(f"/api/v1/patients/{pid}", headers=auth_headers)
    assert r.status_code == 200
    got = r.json()
    assert got["id"] == pid


def test_register_validation(client):
    # Test password muy corto
    r = client.post(
        "/api/v1/auth/register",
        json={
            "username":"test",
            "password":"123"
        }
    )
    assert r.status_code == 422
    errors = r.json()["detail"]
    password_error = next((error for error in errors \
                           if error["loc"][-1] == "password"), None)
    assert password_error is not None
    assert "at least 8" in password_error["msg"].lower()

    # Test nombre de usuario duplicado
    client.post(
        "/api/v1/auth/register",
        json={
            "username":"alice",
            "password":"password123"
        }
    )
    r = client.post(
        "/api/v1/auth/register",
        json={
            "username":"alice",
            "password":"password123"
        }
    )
    assert r.status_code == 400
    message = "El nombre de usuario ya existe"
    assert message in r.json()["detail"]


def test_patient_crud_operations(client, auth_headers):
    # Crear paciente
    patient_data = {"name":"John Doe","age":30,"symptoms":["headache"]}
    r = client.post(
        "/api/v1/patients",
        json=patient_data,
        headers=auth_headers
    )
    assert r.status_code == 201
    patient = r.json()
    patient_id = patient["id"]

    # Actualizar paciente
    update_data = {"age": 31, "symptoms": ["headache", "fever"]}
    r = client.put(
        f"/api/v1/patients/{patient_id}",
        json=update_data,
        headers=auth_headers
    )
    assert r.status_code == 200
    updated = r.json()
    assert updated["age"] == 31
    assert "fever" in updated["symptoms"]

    # Eliminar paciente
    r = client.delete(f"/api/v1/patients/{patient_id}", headers=auth_headers)
    assert r.status_code == 204

    # Verificar eliminación del paciente
    r = client.get(f"/api/v1/patients/{patient_id}", headers=auth_headers)
    assert r.status_code == 404


def test_patient_filtering(client, auth_headers):
    # Crear varios pacientes
    patients = [
        {"name":"Alice","age":25,"symptoms":["fever"]},
        {"name":"Bob","age":35,"symptoms":["cough"]},
        {"name":"Charlie","age":45,"symptoms":["fever","cough"]}
    ]
    
    for patient in patients:
        client.post("/api/v1/patients", json=patient, headers=auth_headers)

    # Test filtro por edad
    r = client.get("/api/v1/patients?min_age=30", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert all(p["age"] >= 30 for p in data["patients"])

    # Test filtro por síntoma
    r = client.get("/api/v1/patients?symptom=fever", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert all("fever" in p["symptoms"] for p in data["patients"])


def test_authentication_required(client):
    # Intentar acceder sin token
    r = client.get("/api/v1/patients")
    assert r.status_code == 401

    r = client.post("/api/v1/patients", json={"name":"Test","age":30})
    assert r.status_code == 401


def test_health_check(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "version" in data
