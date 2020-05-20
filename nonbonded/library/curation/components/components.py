import abc
import logging
from typing import Generic, TypeVar

import pandas
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ComponentSchema(BaseModel, abc.ABC):

    ...


T = TypeVar("T", bound=ComponentSchema)


class Component(Generic[T], abc.ABC):
    @classmethod
    @abc.abstractmethod
    def _apply(
        cls, data_frame: pandas.DataFrame, schema: T, n_processes
    ) -> pandas.DataFrame:
        raise NotImplementedError()

    @classmethod
    def apply(
        cls, data_frame: pandas.DataFrame, schema: T, n_processes=1
    ) -> pandas.DataFrame:
        """Apply this component to a data frame.

        Parameters
        ----------
        data_frame: pandas.DataFrame
            The data frame to apply the component to.
        schema: T
            The schema which defines how this component should be applied.
        n_processes: int
            The number of processes that this component is allowed to
            parallelize across.

        Returns
        -------
        pandas.DataFrame
            The data frame which has had the component applied to it.
        """

        modified_data_frame = cls._apply(data_frame, schema, n_processes)

        n_data_points = len(data_frame)
        n_filtered = len(modified_data_frame)

        if n_filtered != n_data_points:

            direction = "removed" if n_filtered < n_data_points else "added"

            logger.info(
                f"{abs(n_filtered - n_data_points)} data points were {direction} after "
                f"applying the {cls.__name__} component."
            )

        return modified_data_frame