import abc
import logging
from typing import Callable, Type, TypeVar

import requests
from pydantic.main import BaseModel

from nonbonded.library.config import settings

T = TypeVar("T", bound="BaseREST")


class BaseORM(BaseModel, abc.ABC):
    class Config:
        orm_mode = True


class BaseREST(BaseORM, abc.ABC):
    @classmethod
    @abc.abstractmethod
    def _get_endpoint(cls, **kwargs):
        raise NotImplementedError()

    @abc.abstractmethod
    def _post_endpoint(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _put_endpoint(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _delete_endpoint(self):
        raise NotImplementedError()

    def _upload(self, request_function: Callable, url: str) -> T:
        """The internal implementation of the upload and update methods."""
        request = request_function(
            url=url,
            data=self.json(),
            headers={"access_token": settings.ACCESS_TOKEN},
        )

        try:
            request.raise_for_status()
        except requests.exceptions.HTTPError as error:
            logging.exception(error.response.text)
            raise
        except Exception:  # pragma: no cover
            raise

        return_object = self.__class__.parse_raw(request.text)
        return return_object

    def upload(self, requests_class=requests) -> T:
        """Attempt to upload this object to the RESTful API for the first time.
        This function should only be used for the initial upload. To update an
        existing instance, used the ``update`` function instead.

        Objects which have been uploaded to the RESTful API can be easily retrieved
        using ``from_rest`` class function.

        An exception will be raised if the API already contains an instance of this
        object with the same identifiers.

        Notes
        -----
        The RESTful API returns back the object which was posted - this may not be
        identical to the initially submitted object as the API may have assigned /
        changed some of the ids. The returned object should **always** be used in
        place of the initial one.
        """
        return self._upload(requests_class.post, self._post_endpoint())

    def update(self, requests_class=requests) -> T:
        """Attempt to update this object on the RESTful API. This function assumes
        that this object has already been uploaded using the ``upload`` function.

        An exception will be raised if this object has not already been uploaded.
        """
        return self._upload(requests_class.put, self._put_endpoint())

    def delete(self, requests_class=requests):
        """Attempt to delete this object on the RESTful API. This function assumes
        that this object has already been uploaded using the ``upload`` function.

        An exception will be raised if this object has not already been uploaded.
        """

        request = requests_class.delete(
            url=self._delete_endpoint(), headers={"access_token": settings.ACCESS_TOKEN}
        )
        try:
            request.raise_for_status()
        except requests.exceptions.HTTPError as error:
            logging.exception(error.response.text)
            raise
        except Exception:  # pragma: no cover
            raise

    @classmethod
    def from_rest(cls: Type[T], **kwargs) -> T:
        """Attempts to retrieve an instance of this object from the RESTful API
        based on its unique identifier(s)
        """
        requests_class = kwargs.pop("requests_class", requests)
        request = requests_class.get(cls._get_endpoint(**kwargs))

        try:
            request.raise_for_status()
        except requests.exceptions.HTTPError as error:
            logging.exception(error.response.text)
            raise
        except Exception:  # pragma: no cover
            raise

        return cls.parse_raw(request.text)

    def to_file(self, file_path: str):
        """JSON serializes this object and saves the output to the specified
        file path.

        Parameters
        ----------
        file_path: str
            The path to save the JSON serialized object to.
        """

        with open(file_path, "w") as file:
            file.write(self.json())


class BaseRESTCollection(BaseORM, abc.ABC):
    @classmethod
    @abc.abstractmethod
    def _get_endpoint(cls, **kwargs):
        raise NotImplementedError()

    @classmethod
    def from_rest(cls: Type[T], **kwargs) -> T:
        """Attempts to retrieve an instance of this object from the RESTful API
        based on its unique identifier(s)
        """
        requests_class = kwargs.pop("requests_class", requests)
        request = requests_class.get(cls._get_endpoint(**kwargs))

        try:
            request.raise_for_status()
        except requests.exceptions.HTTPError as error:
            logging.exception(error.response.text)
            raise
        except Exception:  # pragma: no cover
            raise

        return cls.parse_raw(request.text)
