from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nonbonded.backend.core.config import settings, DatabaseType

# connect_args={"check_same_thread": False} is required for SQLite
if settings.DATABASE_TYPE == DatabaseType.SQLite:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False}
    )
elif settings.DATABASE_TYPE == DatabaseType.PostgreSql:
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True)

else:
    raise NotImplementedError

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
