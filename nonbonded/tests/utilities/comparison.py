from contextlib import contextmanager
from typing import TypeVar

from deepdiff import DeepDiff

from nonbonded.library.models import BaseORM

T = TypeVar("T", bound=BaseORM)


@contextmanager
def does_not_raise():
    """A helpful context manager to use inplace of a pytest raise statement
    when no exception is expected."""
    yield


def compare_pydantic_models(model_a: T, model_b: T):
    """Compares two pydantic models for equaility.

    Parameters
    ----------
    model_a
        The first model to compare.
    model_b
        The second model to compare.
    """
    difference = DeepDiff(model_a.dict(), model_b.dict(), ignore_order=True)

    if not len(difference) == 0:
        print(difference)

    assert len(difference) == 0
