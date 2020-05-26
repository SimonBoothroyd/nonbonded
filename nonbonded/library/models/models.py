import abc
from typing import TYPE_CHECKING, Type, TypeVar

from pydantic.main import BaseModel

from nonbonded.library.config import settings

T = TypeVar("T", bound="BaseREST")

if TYPE_CHECKING:
    import requests


class BaseORM(BaseModel, abc.ABC):
    class Config:
        orm_mode = True


class BaseREST(BaseORM, abc.ABC):
    @abc.abstractmethod
    def _post_endpoint(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _put_endpoint(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _delete_endpoint(self):
        raise NotImplementedError()

    def upload(self) -> T:
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
        import requests

        request = requests.post(
            url=self._post_endpoint(),
            data=self.json(),
            headers={"access_token": settings.ACCESS_TOKEN},
        )
        request.raise_for_status()

        return_object = self.__class__.parse_raw(request.text)
        return return_object

    def update(self) -> T:
        """Attempt to update this object on the RESTful API. This function assumes
        that this object has already been uploaded using the ``upload`` function.

        An exception will be raised if this object has not already been uploaded.
        """
        import requests

        request = requests.put(
            url=self._put_endpoint(),
            data=self.json(),
            headers={"access_token": settings.ACCESS_TOKEN},
        )
        request.raise_for_status()

        return_object = self.__class__.parse_raw(request.text)
        return return_object

    def delete(self):
        """Attempt to delete this object on the RESTful API. This function assumes
        that this object has already been uploaded using the ``upload`` function.

        An exception will be raised if this object has not already been uploaded.
        """
        import requests

        request = requests.delete(
            url=self._delete_endpoint(), headers={"access_token": settings.ACCESS_TOKEN}
        )
        request.raise_for_status()

    @classmethod
    def _from_rest(cls: Type[T], request: "requests.Response") -> T:
        request.raise_for_status()

        return_object = cls.parse_raw(request.text)
        return return_object

    @classmethod
    @abc.abstractmethod
    def from_rest(cls: Type[T], *args, **kwargs) -> T:
        """Attempts to retrieve an instance of this object from the RESTful API
        based on its unique identifier(s)
        """
        raise NotImplementedError()

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
