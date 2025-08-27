# app/database_utils.py  (nuevo archivo recomendado)
from typing import Tuple, Optional
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool


def make_engine_from_url(
    database_url: str,
    logger: Optional[logging.Logger] = None,
    echo_env_var: str = "SQL_ECHO",
) -> Tuple[Engine, str]:
    """
    Crea y configura un Engine SQLAlchemy según el scheme de `database_url`.
    - Para SQLite: aplica `connect_args`, `StaticPool` y `check_same_thread=False`.
    - Para otros motores (Postgres/MySQL): aplica parámetros de pool más apropiados.

    Devuelve tupla: (engine, mensaje_log).

    Parámetros:
      - database_url: str, URL de conexión a la base de datos.
      - logger: optional Logger. Si se provee, la función hará logger.info(message).
      - echo_env_var: nombre de la variable de entorno que controla `echo` (por defecto "SQL_ECHO").

    Nota: ajusta pool_size / max_overflow según la carga y el motor de BD en producción.
    """
    echo_flag = os.getenv(echo_env_var, "false").lower() == "true"

    if database_url.startswith("sqlite"):
        engine = create_engine(
            database_url,
            echo=echo_flag,
            connect_args={
                "check_same_thread": False,
                "timeout": 30
            },
            poolclass=StaticPool,
            pool_pre_ping=True,
        )
        message = "Usando base de datos SQLite"
    else:
        # Valores razonables por defecto para bases de datos SQL (ajustar según necesidades)
        engine = create_engine(
            database_url,
            echo=echo_flag,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        )
        message = "Usando base de datos SQL estándar"

    if logger is not None:
        logger.info(message)

    return engine, message
