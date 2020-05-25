from enum import Enum
from typing import List, Union

from pydantic import AnyHttpUrl, BaseSettings, validator


class DatabaseType(Enum):

    PostgreSql = "PostgreSql"
    SQLite = "SQLite"


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"

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

    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./nonbonded.db"

    POSTGRESQL_SERVER: str
    POSTGRESQL_USER: str
    POSTGRESQL_PASSWORD: str
    POSTGRESQL_DB: str


settings = Settings()
