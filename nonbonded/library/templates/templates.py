import abc

from nonbonded.library.utilities.exceptions import UnrecognisedKwargsError


class BaseTemplate(abc.ABC):
    @classmethod
    def _check_unrecognised_options(cls, **options):

        if len(options) == 0:
            return

        raise UnrecognisedKwargsError(*options)

    @classmethod
    @abc.abstractmethod
    def generate(cls, **options) -> str:
        raise NotImplementedError()
