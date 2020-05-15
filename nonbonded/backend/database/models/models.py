"""Checks for uniqueness based on the example here:

    https://github.com/sqlalchemy/sqlalchemy/wiki/UniqueObject

"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query

Base = declarative_base()


def _unique(session, cls, hash_function, query_function, constructor, kwargs):

    cache = getattr(session, "_unique_cache", None)

    if cache is None:
        session._unique_cache = cache = {}

    key = (cls, hash_function(**kwargs))

    if key in cache:

        return cache[key]

    else:

        with session.no_autoflush:

            exists_query = session.query(cls)
            exists_query = query_function(exists_query, **kwargs)

            obj = exists_query.first()

            if not obj:

                obj = constructor(**kwargs)
                session.add(obj)

        cache[key] = obj
        return obj


class UniqueMixin(object):
    @classmethod
    def unique_hash(cls, **kwargs):
        raise NotImplementedError()

    @classmethod
    def unique_filter(cls, query: Query, **kwargs):
        raise NotImplementedError()

    @classmethod
    def as_unique(cls, session, **kwargs):

        return _unique(session, cls, cls.unique_hash, cls.unique_filter, cls, kwargs)
