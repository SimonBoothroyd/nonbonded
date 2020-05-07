from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nonbonded.backend.core.config import settings

# connect_args={"check_same_thread": False} is required for SQLite
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
