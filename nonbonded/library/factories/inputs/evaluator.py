from typing import TYPE_CHECKING, List, Union

from pydantic import BaseModel, Field
from typing_extensions import Literal

if TYPE_CHECKING:
    from openff.evaluator import backends
    from openff.evaluator.backends import dask

    PositiveInt = int

else:
    from pydantic import PositiveInt


class ComputeResources(BaseModel):

    n_processes: PositiveInt = Field(
        1, description="The number of processes to request per calculation worker."
    )
    n_gpus: int = Field(
        1, description="The number of GPUs to request per calculation worker."
    )

    def to_evaluator(self) -> "backends.ComputeResources":

        from openff.evaluator import backends

        evaluator_resources = backends.ComputeResources(
            number_of_threads=self.n_processes, number_of_gpus=self.n_gpus
        )

        return evaluator_resources


class QueueWorkerResources(ComputeResources):

    memory_limit: PositiveInt = Field(
        5, description="The amount of memory to request per worker (GB)."
    )
    wallclock_time_limit: str = Field(
        "05:59",
        description="The maximum amount of wall clock time that a worker can run for. "
        "This should be a string of the form `HH:MM` where HH is the number of hours "
        "and MM the number of minutes",
    )

    def to_evaluator(self) -> "backends.QueueWorkerResources":

        from openff.evaluator import backends, unit

        evaluator_resources = backends.QueueWorkerResources(
            number_of_threads=self.n_processes,
            number_of_gpus=self.n_gpus,
            preferred_gpu_toolkit=backends.ComputeResources.GPUToolkit.CUDA,
            per_thread_memory_limit=self.memory_limit * unit.gigabytes,
            wallclock_time_limit=self.wallclock_time_limit,
        )

        return evaluator_resources


class DaskHPCClusterConfig(BaseModel):

    type: Literal["dask-hpc"] = Field("dask-hpc")

    cluster_type: Literal["lsf"] = Field(
        "lsf", description="The type queueing system available on the cluster."
    )

    minimum_workers: PositiveInt = Field(
        1, description="The minimum number of calculation workers to request"
    )
    maximum_workers: PositiveInt = Field(
        1, description="The maximum number of calculation workers to request"
    )

    resources_per_worker: QueueWorkerResources = Field(
        ..., description="The amount of resources to request per worker."
    )
    queue_name: str = Field(
        ...,
        description="The name of the queue which the workers will be requested from.",
    )

    setup_script_commands: List[str] = Field(
        default_factory=list,
        description="A list of bash script commands to call within the queue "
        "submission script before the call to launch the dask worker. This may include "
        "activating a python environment, or loading an environment module",
    )

    def to_evaluator(self) -> "dask.DaskLSFBackend":

        from openff.evaluator.backends import dask

        evaluator_backend = dask.DaskLSFBackend(
            minimum_number_of_workers=self.minimum_workers,
            maximum_number_of_workers=self.maximum_workers,
            resources_per_worker=self.resources_per_worker.to_evaluator(),
            queue_name=self.queue_name,
            setup_script_commands=self.setup_script_commands,
            adaptive_interval="1000ms",
        )

        return evaluator_backend


class DaskLocalClusterConfig(BaseModel):

    type: Literal["dask-local"] = Field("dask-local")

    number_of_workers: PositiveInt = Field(
        1, description="The number of calculation workers to request"
    )
    resources_per_worker: ComputeResources = Field(
        ..., description="The amount of resources to request per worker."
    )

    def to_evaluator(self):

        from openff.evaluator.backends import dask

        evaluator_backend = dask.DaskLocalCluster(
            number_of_workers=self.number_of_workers,
            resources_per_worker=self.resources_per_worker.to_evaluator(),
        )

        return evaluator_backend


class EvaluatorServerConfig(BaseModel):

    backend_config: Union[DaskLocalClusterConfig, DaskHPCClusterConfig] = Field(
        ...,
        description="The configuration of the calculation backend to use for the "
        "server.",
    )

    port: int = Field(8000, description="The port to use for the server.")

    working_directory: str = Field(
        "working-directory",
        description="The directory in which to store any working files and directories",
    )

    def to_backend(self):
        return self.backend_config.to_evaluator()

    def to_server(self, evaluator_backend):

        from openff.evaluator import server

        evaluator_server = server.EvaluatorServer(
            calculation_backend=evaluator_backend,
            working_directory=self.working_directory,
            port=self.port,
        )

        return evaluator_server
