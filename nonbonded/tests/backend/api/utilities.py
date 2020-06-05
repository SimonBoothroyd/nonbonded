import abc
import copy
from typing import Callable, Dict, Tuple, Type, TypeVar

import pytest
from fastapi.testclient import TestClient
from requests import HTTPError
from sqlalchemy.orm import Session

from nonbonded.library.models import BaseREST
from nonbonded.library.utilities.exceptions import UnsupportedEndpointError

T = TypeVar("T", bound="BaseREST")


class BaseTestEndpoints(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def _rest_class(cls) -> Type[BaseREST]:
        """The model class associated with the endpoints to test."""
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _create_model(
        cls, db: Session, create_dependencies: bool = True
    ) -> Tuple[T, Dict[str, str]]:
        """Creates an instance of the model represented by the endpoints
        being tested but does not commit it to the database. Optionally,
        this function can also commit any parents / dependencies to the database
        which would be required to store the created model.

        Parameters
        ----------
        db
            The current database session.
        create_dependencies
            Whether to commit any of the associated parents / dependencies
            to the database while creating this model.

        Returns
        -------
            The created model.

            The keys which uniquely identify the model.
        """
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _perturb_model(cls, model: T):
        """Perturbs a specified model in such a way so as to
        constitute an 'updated' model.

        Parameters
        ----------
        model
            The model to perturb.
        """
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _commit_model(cls, db: Session) -> Tuple[T, Dict[str, str]]:
        """Commit the model represented by the endpoints
        being tested to the database, so that it can be
        read, updated or deleted.

        Parameters
        ----------
        db
            The current database session.

        Returns
        -------
            The model which has been committed to the database.

            The keys which uniquely identify the model in the database.
        """
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _comparison_function(cls) -> Callable[[T, T], None]:
        """A function which compares if two models of the type represented
        by this endpoint are equivalent. This function should raise an
        ``AssertionError`` when this isn't the case.
        """
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _n_db_models(cls, db: Session) -> int:
        """Returns the number of models of the type represented
        by this endpoint which are stored in the database.

        Parameters
        ----------
        db
            The current database session.
        """
        raise NotImplementedError()

    def test_get(self, rest_client: TestClient, rest_db: Session):

        model, model_keys = self._commit_model(rest_db)

        rest_model = self._rest_class().from_rest(
            **model_keys, requests_class=rest_client
        )

        self._comparison_function()(model, rest_model)

    def test_post(self, rest_client: TestClient, rest_db: Session):

        model, _ = self._create_model(rest_db)
        rest_model = self._rest_class().upload(model, rest_client)

        self._comparison_function()(model, rest_model)

    def test_put(self, rest_client: TestClient, rest_db: Session):

        original_model, _ = self._commit_model(rest_db)

        updated_model = copy.deepcopy(original_model)
        self._perturb_model(updated_model)

        try:
            rest_model = self._rest_class().update(updated_model, rest_client)

            with pytest.raises(AssertionError):
                self._comparison_function()(original_model, rest_model)

        except UnsupportedEndpointError:
            pytest.skip("Unsupported endpoint.")
            raise
        except Exception:
            raise

        self._comparison_function()(updated_model, rest_model)

    def test_delete(self, rest_client: TestClient, rest_db: Session):

        model, _ = self._commit_model(rest_db)
        assert self._n_db_models(rest_db) == 1

        self._rest_class().delete(model, requests_class=rest_client)
        assert self._n_db_models(rest_db) == 0

    def test_not_found(self, rest_client: TestClient, rest_db: Session):

        model, model_keys = self._create_model(rest_db, False)

        with pytest.raises(HTTPError) as error_info:
            self._rest_class().from_rest(**model_keys, requests_class=rest_client)

        assert error_info.value.response.status_code == 404

        with pytest.raises(HTTPError) as error_info:
            self._rest_class().delete(model, requests_class=rest_client)

        assert error_info.value.response.status_code == 404

        try:
            with pytest.raises(HTTPError) as error_info:
                self._rest_class().update(model, rest_client)

            assert error_info.value.response.status_code == 404

        except UnsupportedEndpointError:
            pass
        except Exception:
            raise
