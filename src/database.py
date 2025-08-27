import logging
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from .settings import get_settings
from .database_utils import make_engine_from_url


# Obtener configuración
settings = get_settings()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener URL de la base de datos desde la configuración
DATABASE_URL = settings.database_url

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
            session.execute("SELECT 1")
        return True
    except Exception as e:
        message = "Conexión a la base de datos fallida"
        logger.error(f"{message}: {e}")
        return False
