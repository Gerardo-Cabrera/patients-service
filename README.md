# API de Pacientes (FastAPI + SQLite) con autenticación, pruebas y CI

Este proyecto proporciona una API REST completa para registrar y consultar pacientes y sus síntomas.
Incluye autenticación JWT, tests unitarios/integración (pytest + httpx) y un workflow de GitHub Actions
para ejecutar tests automáticamente.

## 🚀 Características

- **FastAPI + SQLModel** (SQLite/PostgreSQL)
- **Autenticación JWT** (registro + login)
- **Endpoints protegidos** para CRUD de pacientes
- **Filtrado y paginación** avanzada
- **Validación de datos** robusta
- **Tests completos** usando pytest y httpx AsyncClient
- **Docker** listo para producción
- **CI/CD** con GitHub Actions
- **CORS** configurado
- **Logging** y manejo de errores
- **Health checks**

## 🛠️ Instalación y Ejecución

### 1. Configuración del entorno

```bash
# Clonar el repositorio
git clone <repository-url>
cd patients-service

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
pip install -e .
```

### 2. Configuración de variables de entorno

Crear archivo `.env` basado en `.env.example`:

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar variables según necesidades
nano .env
```

### 3. Ejecutar la aplicación

#### Opción A: Ejecución local (recomendado para desarrollo)

```bash
# Opción 1: Usando el script
./run.sh

# Opción 2: Directamente con uvicorn
uvicorn src.main:src --reload --host 0.0.0.0 --port 8000
```

#### Opción B: Ejecución con Docker

```bash
# Construir imagen
docker build -t patients-api .

# Ejecutar contenedor (SQLite)
docker run -p 8000:8000 -v $(pwd)/data_files:/src/data_files --env-file .env patients-api
```

**Nota**: La base de datos SQLite se crea automáticamente en el directorio `./data_files/` cuando se ejecuta la aplicación por primera vez.

#### Opción C: Docker Compose (solo para PostgreSQL)

Si prefieres usar PostgreSQL en lugar de SQLite:

```bash
# Crear docker-compose.yml para PostgreSQL
cat > docker-compose.yml << EOF
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://patients_user:patients_pass@db:5432/patients_db
      - SECRET_KEY=your-secret-key
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: patients_db
      POSTGRES_USER: patients_user
      POSTGRES_PASSWORD: patients_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
EOF

# Ejecutar con PostgreSQL
docker-compose up -d
```

### 4. Acceder a la documentación

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 🔐 Autenticación

### Registro de usuario
```bash
POST /api/v1/auth/register
Content-Type: application/x-www-form-urlencoded

username=usuario&password=contraseña123
```

### Login
```bash
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=usuario&password=contraseña123
```

**Respuesta:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Usar token en requests
```bash
Authorization: Bearer <access_token>
```

## 📋 Endpoints de Pacientes

### Crear paciente
```bash
POST /api/v1/patients
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Juan Pérez",
  "age": 35,
  "symptoms": ["fiebre", "tos"]
}
```

### Listar pacientes (con filtros)
```bash
GET /api/v1/patients?name=Juan&min_age=30&max_age=40&symptom=fiebre&offset=0&limit=10
Authorization: Bearer <token>
```

**Parámetros de filtrado:**
- `name`: Filtrar por nombre (búsqueda parcial)
- `min_age`: Edad mínima
- `max_age`: Edad máxima
- `symptom`: Filtrar por síntoma
- `offset`: Desplazamiento para paginación
- `limit`: Límite de resultados (máx. 1000)

### Obtener paciente por ID
```bash
GET /api/v1/patients/{id}
Authorization: Bearer <token>
```

### Actualizar paciente
```bash
PUT /api/v1/patients/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "age": 36,
  "symptoms": ["fiebre", "tos", "dolor de cabeza"]
}
```

### Eliminar paciente
```bash
DELETE /api/v1/patients/{id}
Authorization: Bearer <token>
```

### Health check
```bash
GET /api/v1/health
```

## 🧪 Tests

### Ejecutar tests
```bash
# Ejecutar todos los tests
pytest -v

# Ejecutar tests con coverage
pytest --cov=app tests/

# Ejecutar tests específicos
pytest tests/test_api.py::test_patient_crud_operations
```

### Tests incluidos
- ✅ Registro y autenticación
- ✅ CRUD completo de pacientes
- ✅ Filtrado y paginación
- ✅ Validaciones de datos
- ✅ Autenticación requerida
- ✅ Health checks

## 🐳 Docker

### ¿Cuándo usar Docker?

- **Desarrollo local**: Usa **ejecución local** (Opción A) - más rápido y simple
- **Despliegue simple**: Usa **Docker con SQLite** (Opción B) - para aplicaciones pequeñas
- **Producción**: Usa **Docker Compose con PostgreSQL** (Opción C) - para aplicaciones en producción

### Configuración avanzada

#### Variables de entorno para Docker

```bash
# Para desarrollo con SQLite
docker run -p 8000:8000 \
  -v $(pwd)/data:/src/data \
  -e DATABASE_URL=sqlite:///./data/patients.db \
  -e SECRET_KEY=dev-secret-key \
  patients-api

# Para producción con PostgreSQL
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/patients \
  -e SECRET_KEY=your-production-secret-key \
  -e ACCESS_TOKEN_EXPIRE_MINUTES=30 \
  patients-api
```

#### Optimización de imagen Docker

```dockerfile
# Dockerfile optimizado para producción
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# Copiar requirements primero para cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Crear directorio para datos
RUN mkdir -p /src/data && chmod 755 /src/data

# Usuario no-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /src
USER appuser

EXPOSE 8000
CMD ["uvicorn", "src.main:src", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔧 Configuración

### Variables de entorno principales

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `DATABASE_URL` | URL de conexión a BD | `sqlite:///./patients.db` |
| `SECRET_KEY` | Clave secreta para JWT | `change-me-for-prod` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiración de tokens | `60` |
| `CORS_ORIGINS` | Orígenes permitidos | `["http://localhost:3000"]` |

### Base de datos

**SQLite (desarrollo):**
```bash
DATABASE_URL=sqlite:///./patients.db
```

**PostgreSQL (producción):**
```bash
DATABASE_URL=postgresql://user:password@localhost/patients_db
```

## 📊 Estructura del Proyecto

```
patients-service/
├── src/
│   ├── __init__.py
│   ├── main.py          # Endpoints principales
│   ├── models.py        # Modelos de datos
│   ├── crud.py          # Operaciones de BD
│   ├── auth.py          # Autenticación JWT
│   ├── database.py      # Configuración de BD
│   ├── schemas.py       # Esquemas Pydantic
│   └── config.py        # Configuración centralizada
├── tests/
│   └── test_api.py      # Tests de la API
├── requirements.txt     # Dependencias
├── Dockerfile          # Configuración Docker
├── pytest.ini         # Configuración pytest
└── README.md          # Documentación
```
