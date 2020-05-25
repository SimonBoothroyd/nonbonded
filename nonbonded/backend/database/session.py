from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nonbonded.backend.core.config import DatabaseType, settings

if settings.DATABASE_TYPE == DatabaseType.SQLite:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False}
    )
elif settings.DATABASE_TYPE == DatabaseType.PostgreSql:
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)

else:
    raise NotImplementedError

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
