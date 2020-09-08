"""The fixtures found here are based on a number of StackOverflow posts which
are succinctly summarised here:

https://gist.github.com/kissgyorgy/e2365f25a213de44b9a2
"""
import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from nonbonded.backend.app import app
from nonbonded.backend.database.models import Base
from nonbonded.backend.database.session import SessionLocal


@pytest.yield_fixture
def db() -> Session:

    session = SessionLocal()
    Base.metadata.create_all(session.get_bind())

    yield session

    Base.metadata.drop_all(session.get_bind())
    session.rollback()

    session.close()


@pytest.yield_fixture
def rest_client(db) -> TestClient:
    """Returns FastAPI test client."""

    with TestClient(app) as client:
        yield client
