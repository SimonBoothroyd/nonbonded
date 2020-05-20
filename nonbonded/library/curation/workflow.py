from typing import List, Union

import pandas
from pydantic import BaseModel, Field

from nonbonded.library.curation.components.filtering import FilterComponentSchema
from nonbonded.library.curation.components.processing import ProcessComponentSchema
from nonbonded.library.curation.components.selection import SelectionComponentSchema
from nonbonded.library.models.datasets import Component


class WorkflowSchema(BaseModel):

    component_schemas: List[
        Union[FilterComponentSchema, ProcessComponentSchema, SelectionComponentSchema]
    ] = Field(
        default_factory=list,
        description="The schemas of the components to apply as part of this workflow. "
        "The components will be applied in the order they appear in this list.",
    )


class Workflow:
    @classmethod
    def apply(
        cls, data_frame: pandas.DataFrame, schema: WorkflowSchema, n_processes=1
    ) -> pandas.DataFrame:
        """Apply each component of this workflow to an initial data frame in
        sequence.

        Parameters
        ----------
        data_frame: pandas.DataFrame
            The data frame to apply the workflow to.
        schema: WorkflowSchema
            The schema which defines the components to apply.
        n_processes: int
            The number of processes that each component is allowed to
            parallelize across.

        Returns
        -------
        pandas.DataFrame
            The data frame which has had the components applied to it.
        """

        component_classes = {
            class_type.__name__: class_type for class_type in Component.__subclasses__()
        }

        for component_schema in schema.component_schemas:

            component_class_name = component_schema.__name__.replace("Schema", "")
            component_class = component_classes[component_class_name]

            data_frame = component_class.apply(
                data_frame, component_schema, n_processes
            )

        return data_frame
