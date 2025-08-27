from pydantic import SecretStr, Field, field_validator
from pydantic_settings import BaseSettings
from typing import Any, Callable, Dict, Tuple


class Settings(BaseSettings):
    secret_key: SecretStr = Field(
        ...,
        description="Clave secreta para JWT"
    )
    access_token_expire_minutes: int = Field(
        ...,
        description="Minutos para que expire el token de acceso"
    )
    database_url: str = Field(
        ...,
        description="URL de conexión a la base de datos"
    )
    environment: str = Field(
        ...,
        description="Entorno: development, staging, production"
    )
    debug: bool = Field(False, description="Modo debug")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


    # Validadores para transformar/validar valores de entorno
    @field_validator("access_token_expire_minutes", mode="before")
    def _parse_access_token_minutes(cls, v):
        # Convierte/valida que '' ya fue filtrado por 
        # settings_customise_sources
        if isinstance(v, str):
            s = v.strip()
            try:
                return int(s)
            except Exception as exc:
                message = "ACCESS_TOKEN_EXPIRE_MINUTES debe ser un entero"
                raise ValueError(message) from exc
        return int(v)


    @field_validator("debug", mode="before")
    def _parse_debug(cls, v):
        if isinstance(v, str):
            s = v.strip().lower()
            return s in ("1", "true", "yes", "on")
        return bool(v)


    @field_validator("database_url", mode="before")
    def _parse_database_url(cls, v):
        # No establece valor por defecto; sólo normaliza strings
        if isinstance(v, str):
            return v.strip()
        return v
    
    # Personalizar fuentes de configuración para filtrar 
    # variables de entorno y mapear a minúsculas, ignorando 
    # valores nulos o vacíos.
    @classmethod
    def settings_customise_sources(
        cls,
        *args,
        **kwargs
    ) -> Tuple[
        Callable[..., Dict[str, Any]],
        Callable[..., Dict[str, Any]],
        Callable[..., Dict[str, Any]]
    ]:
        # Extraer los callables init_settings, env_settings, 
        # file_secret_settings de args/kwargs
        init_settings = None
        env_settings = None
        file_secret_settings = None

        # Primero intentar por posición
        if len(args) >= 3:
            init_settings,
            env_settings,
            file_secret_settings = args[:3]
        else:
            # Intentar por nombre
            init_settings = kwargs.get("init_settings")
            env_settings = kwargs.get("env_settings")
            file_secret_settings = kwargs.get("file_secret_settings")

        # Si aún falta alguno, mostrar error
        if init_settings is None \
            or env_settings is None \
            or file_secret_settings is None:
            message = (
                "Fuentes de configuración no pudieron ser determinadas."
            )
            raise RuntimeError(message)
        
        # Envolver env_settings para filtrar y mapear a minúsculas
        def _filtered_env(*f_args, **f_kwargs) -> Dict[str, Any]:
            try:
                raw = env_settings(*f_args, **f_kwargs) or {}
            except TypeError:
                # Intentar llamar sin argumentos si la firma espera 0
                raw = env_settings() or {}
                
            mapped: Dict[str, Any] = {}

            for env_name, value in raw.items():
                # Ignorar valores nulos o strings vacíos
                if value is None or \
                    (isinstance(value, str) and value.strip() == ""):
                    continue

                # Mapear a minúsculas para pydantic
                mapped_key = env_name.lower()
                mapped[mapped_key] = value
            return mapped

        return init_settings, _filtered_env, file_secret_settings



_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()

        if not _settings.secret_key.get_secret_value():
            message = "SECRET_KEY es obligatorio y \
                no puede estar vacío."
            raise RuntimeError(message)
    return _settings
