import logging
from typing import Generator
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
from .settings import get_settings
from .database_utils import make_engine_from_url


# Obtener configuración
settings = get_settings()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener URL de la base de datos desde la configuración
DATABASE_URL = settings.database_url
logger.info("DATABASE_URL=%s", DATABASE_URL)

# Si se usa SQLite en forma de archivo, asegúrate de que la carpeta exista
if DATABASE_URL.startswith("sqlite"):
    try:
        sqlite_path = DATABASE_URL.split("///", 1)[-1]
        if sqlite_path and not sqlite_path.startswith(":memory:"):
            db_file = Path(sqlite_path)
            db_dir = db_file.parent
            if not db_dir.exists():
                logger.info("Creando directorio para SQLite: %s", db_dir)
                db_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        message = "Error creando el directorio para la base de datos SQLite"
        logger.warning(f"{message}: %s", e)

# Crear y configurar el engine de la base de datos
engine, db_message = make_engine_from_url(DATABASE_URL, logger=logger)


def init_db() -> None:
    """Inicializar la base de datos y crear tablas"""
    try:
        SQLModel.metadata.create_all(engine)
        message = "Base de datos y tablas creadas correctamente"
        logger.info(message)
    except Exception as e:
        message = "Error creando la base de datos y las tablas"
        logger.error(f"{message}: {e}")
        raise


def get_session() -> Generator[Session, None, None]:
    """Obtener una sesión de base de datos"""
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            message = "Error en la sesión de la base de datos"
            logger.error(f"{message}: {e}")
            session.rollback()
            raise
        finally:
            session.close()


def check_db_connection() -> bool:
    """Verificar la conexión a la base de datos"""
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        return True
    except Exception as e:
        message = "Conexión a la base de datos fallida"
        logger.error(f"{message}: {e}")
        return False
