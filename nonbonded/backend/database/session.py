from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nonbonded.backend.core.config import settings, DatabaseType

# connect_args={"check_same_thread": False} is required for SQLite
if settings.DATABASE_TYPE == DatabaseType.SQLite:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False}
    )
elif settings.DATABASE_TYPE == DatabaseType.PostgreSql:

    engine = create_engine(
        "postgresql://"
        f"{settings.POSTGRESQL_USER}:{settings.POSTGRESQL_PASSWORD}"
        "@"
        f"{settings.POSTGRESQL_SERVER}/"
        f"{settings.POSTGRESQL_DB}",
        echo=True
    )

else:
    raise NotImplementedError

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
