from typing import Sized


def not_empty(collection: Sized) -> Sized:
    assert len(collection) > 0
    return collection
