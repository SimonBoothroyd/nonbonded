import secrets
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, AnyUrl, BaseSettings, PostgresDsn, validator


class DatabaseType(Enum):

    PostgreSql = "PostgreSql"
    SQLite = "SQLite"


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    ACCESS_TOKEN: str = secrets.token_urlsafe(32)

    PROJECT_NAME: str = "nonbonded"

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:4200"]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:

        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]

        elif isinstance(v, (list, str)):
            return v

        raise ValueError(v)

    DATABASE_TYPE: DatabaseType = DatabaseType.PostgreSql

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    SQLALCHEMY_DATABASE_URI: Optional[AnyUrl] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:

        if isinstance(v, str):
            return v

        if (
            values.get("DATABASE_TYPE") != DatabaseType.PostgreSql
            and values.get("DATABASE_TYPE") != "PostgreSql"
        ):
            raise NotImplementedError()

        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )


settings = Settings()
