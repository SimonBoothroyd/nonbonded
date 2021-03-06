"""The fixtures found here are based on a number of StackOverflow posts which
are succinctly summarised here:

https://gist.github.com/kissgyorgy/e2365f25a213de44b9a2
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nonbonded.backend.core.config import settings as database_settings
from nonbonded.backend.database.models import Base


@pytest.fixture(scope="module")
def engine():
    return create_engine(database_settings.DATABASE_URL, echo=False)


@pytest.yield_fixture(scope="module")
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
    session = Session(bind=connection, autocommit=False, autoflush=False)
    yield session
    session.close()

    # Roll back the broader transaction to ensure a clean state.
    transaction.rollback()

    # Release the connection.
    connection.close()
