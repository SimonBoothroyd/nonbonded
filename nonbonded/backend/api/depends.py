from typing import Generator

from nonbonded.backend.database.session import SessionLocal


def get_db() -> Generator:

    db = None

    try:

        db = SessionLocal()
        yield db

    finally:

        if db is not None:
            db.close()
