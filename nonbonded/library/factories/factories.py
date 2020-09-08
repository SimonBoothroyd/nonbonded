import abc
import logging
import os
from typing import Iterable, Optional, Tuple, Type, TypeVar, Union

from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study
from nonbonded.library.utilities import temporary_cd

logger = logging.getLogger(__name__)

T = TypeVar("T")
S = TypeVar("S")


class BaseFactory(abc.ABC):
    """A generic base class for other factories."""

    @classmethod
    @abc.abstractmethod
    def generate(cls, model: T, **kwargs) -> None:
        pass


class BaseRecursiveFactory(BaseFactory, abc.ABC):
    """A base class for factories which are replied recursively to nested models."""

    @classmethod
    @abc.abstractmethod
    def model_type_to_factory(
        cls, model_type: Type[Union[Project, Study, Optimization, Benchmark]]
    ):
        """Returns the factory which corresponds to a particular model type."""
        raise NotImplementedError()

    @classmethod
    def _yield_child_factory(
        cls, parent: Optional[T]
    ) -> Iterable[Tuple[S, "BaseRecursiveFactory"]]:
        """Temporarily navigates into the parent directory of each child of
        a model (creating it if it doesn't exist) and then yields the child
        and its corresponding factory.

        Parameters
        ----------
        parent
            The parent model
        """

        if isinstance(parent, Project):
            children = parent.studies
        elif isinstance(parent, Study):
            children = [*parent.optimizations, *parent.benchmarks]
        elif isinstance(parent, (Optimization, Benchmark)):
            return
        else:
            raise NotImplementedError()

        for child in children:
            yield child, cls.model_type_to_factory(type(child))

    @classmethod
    @abc.abstractmethod
    def _generate(cls, **kwargs):
        """The internal implementation of ``generate``."""

    @classmethod
    def generate(cls, **kwargs):
        """Apply factories in a recursive manner."""

        parent = kwargs["model"]

        os.makedirs(parent.id, exist_ok=True)

        with temporary_cd(parent.id):

            cls._generate(**kwargs)

            for child, factory in cls._yield_child_factory(parent):

                child_directory_names = {
                    Study: "studies",
                    Optimization: "optimizations",
                    Benchmark: "benchmarks",
                }

                child_directory = child_directory_names[type(child)]
                os.makedirs(child_directory, exist_ok=True)

                with temporary_cd(child_directory):

                    logger.info(
                        f"Applying the {factory.__name__} to "
                        f"{child.__class__.__name__.lower()}={child.id}"
                    )

                    factory.generate(**{**kwargs, "model": child})
