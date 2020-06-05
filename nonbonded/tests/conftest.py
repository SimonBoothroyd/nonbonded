"""The fixtures found here are based on a number of StackOverflow posts which
are succinctly summarised here:

https://gist.github.com/kissgyorgy/e2365f25a213de44b9a2
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from nonbonded.backend.app import app
from nonbonded.backend.core.config import settings as database_settings
from nonbonded.backend.database.models import Base
from nonbonded.backend.database.session import SessionLocal


@pytest.fixture(scope="session")
def engine():
    return create_engine(database_settings.DATABASE_URL, echo=False)


@pytest.yield_fixture(scope="session")
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.yield_fixture
def db(engine, tables) -> Session:
    """Returns a new SqlAlchemy session which will be properly disposed of once
    the tests have completed."""

    connection = engine.connect()
    # Use a separate transaction in case any of the tests perform nested
    # commits. These need to be rollbacked so that successive tests can
    # start from a clean state.
    transaction = connection.begin()

    # Use the connection with the already started transaction
    session = Session(bind=connection)
    yield session
    session.close()

    # Roll back the broader transaction to ensure a clean state.
    transaction.rollback()

    # Release the connection.
    connection.close()


@pytest.yield_fixture
def rest_db() -> Session:

    session = SessionLocal()
    Base.metadata.create_all(session.get_bind())

    yield session

    Base.metadata.drop_all(session.get_bind())
    session.rollback()

    session.close()


@pytest.yield_fixture
def rest_client(rest_db) -> TestClient:
    """Returns FastAPI test client."""

    with TestClient(app) as client:
        yield client
