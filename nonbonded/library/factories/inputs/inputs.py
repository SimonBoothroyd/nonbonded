import logging
import os
from typing import Iterable, List, Optional, Tuple, Type, TypeVar, Union

from nonbonded.library.factories.inputs.evaluator import (
    ComputeResources,
    DaskHPCClusterConfig,
    DaskLocalClusterConfig,
    EvaluatorServerConfig,
    QueueWorkerResources,
)
from nonbonded.library.models.datasets import DataSet, QCDataSet
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study
from nonbonded.library.models.results import OptimizationResult
from nonbonded.library.templates.submission import Submission, SubmissionTemplate
from nonbonded.library.utilities import temporary_cd

logger = logging.getLogger(__name__)

T = TypeVar("T")
S = TypeVar("S")


class InputFactory:
    """A factory used to create the directory structure and inputs for a particular
    model (project, study, optimization or benchmark).
    """

    @classmethod
    def model_type_to_factory(cls, model_type):

        from nonbonded.library.factories.inputs.benchmark import BenchmarkInputFactory
        from nonbonded.library.factories.inputs.optimization import (
            OptimizationInputFactory,
        )

        if issubclass(model_type, (Project, Study)):
            return InputFactory
        elif issubclass(model_type, Optimization):
            return OptimizationInputFactory
        elif issubclass(model_type, Benchmark):
            return BenchmarkInputFactory

        raise NotImplementedError()

    @classmethod
    def _yield_child_factory(
        cls, parent: Optional[T]
    ) -> Iterable[Tuple[S, "InputFactory"]]:
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
    def _find_or_retrieve_data_sets(
        cls,
        data_set_ids: List[str],
        data_set_type: Union[Type[DataSet], Type[QCDataSet]],
        local_data_sets: Optional[List[Union[DataSet, QCDataSet]]],
    ) -> List[Union[DataSet, QCDataSet]]:
        """Attempts to retrieve a list of data sets by their ids from a list of local
        data sets and, if not found, from the remote RESTful API.

        Parameters
        ----------
        data_set_ids: The ids of the data sets to find.
        data_set_type: The type of data set to find.
        local_data_sets: The locally available data sets.

        Returns
        -------
            The found data sets.
        """

        found_ids = (
            set()
            if local_data_sets is None
            else {
                data_set.id
                for data_set in local_data_sets
                if isinstance(data_set, data_set_type)
            }
        )
        expected_ids = {*data_set_ids}

        data_sets = (
            []
            if local_data_sets is None
            else [
                data_set
                for data_set in local_data_sets
                if data_set.id in expected_ids and isinstance(data_set, data_set_type)
            ]
        )
        data_sets.extend(
            data_set_type.from_rest(
                **{
                    (
                        "data_set_id" if data_set_type == DataSet else "qc_data_set_id"
                    ): data_set_id
                }
            )
            for data_set_id in (expected_ids - found_ids)
        )

        return data_sets

    @classmethod
    def _generate_evaluator_config(
        cls, preset_name: str, conda_environment: str, n_workers: int, port: int
    ) -> EvaluatorServerConfig:
        """Generates an Evaluator server configuration."""

        if preset_name == "lilac-local":

            backend_config = DaskLocalClusterConfig(
                resources_per_worker=ComputeResources()
            )

        elif preset_name == "lilac-dask":

            # noinspection PyTypeChecker
            backend_config = DaskHPCClusterConfig(
                maximum_workers=n_workers,
                resources_per_worker=QueueWorkerResources(),
                queue_name="gpuqueue",
                setup_script_commands=[
                    f"conda activate {conda_environment}",
                    "module load cuda/10.1",
                ],
            )

        else:
            raise NotImplementedError()

        server_config = EvaluatorServerConfig(backend_config=backend_config, port=port)

        return server_config

    @classmethod
    def _generate_submission_script(
        cls,
        job_name: str,
        conda_environment: str,
        evaluator_preset: str,
        max_time: str,
        commands: List[str],
    ):
        """Generates an LSF bash submission script.

        Parameters
        ----------
        job_name
            The name of the LSF job.
        conda_environment
            The name of the conda environment to run within.
        max_time
            The maximum wall-clock time for job submissions.
        evaluator_preset
            The present evaluator compute settings to use.
        commands
            The commands to run in the script.
        """

        submission = Submission(
            job_name=job_name,
            wall_clock_limit=max_time,
            max_memory=8,
            gpu=evaluator_preset == "lilac-local",
            environment_name=conda_environment,
            commands=commands,
        )
        with open("submit.sh", "w") as file:
            file.write(SubmissionTemplate.generate("submit_lilac.txt", submission))

    @classmethod
    def _generate(
        cls,
        model: T,
        conda_environment: str,
        max_time: str,
        evaluator_preset: str,
        evaluator_port: int,
        n_evaluator_workers: int,
        include_results: bool,
        reference_data_sets: Optional[List[Union[DataSet, QCDataSet]]],
        optimization_result: Optional[OptimizationResult],
    ):
        """The internal implementation of ``generate``.

        Parameters
        ----------
        model
            The model to generate the inputs for.
        conda_environment
            The name of the conda environment to run within.
        max_time
            The maximum wall-clock time for job submissions.
        evaluator_preset
            The present evaluator compute settings to use.
        evaluator_port
            The port to run the evaluator server on.
        n_evaluator_workers
            The target number of evaluator compute workers to spawn.
        include_results
            Whether to also download any previously generated results
            and store them alongside the inputs.
        reference_data_sets
            The reference data sets referenced by the model
        optimization_result
            The result of the optimization (if any) referenced by the model.
        """

        with open("README.md", "w") as file:
            file.write(model.description)

        if isinstance(model, (Optimization, Benchmark)):

            assert (
                model.optimization_id is None
                or (model.optimization_id is not None and optimization_result is None)
                or (
                    model.optimization_id is not None
                    and optimization_result is not None
                    and model.optimization_id == optimization_result.id
                    and model.study_id == optimization_result.study_id
                    and model.project_id == optimization_result.project_id
                )
            ), (
                f"the provided optimization result does not match the one expected: "
                f"project_id={model.project_id} study_id={model.study_id} "
                f"id={model.optimization_id}"
            )

        if reference_data_sets is not None:

            unique_ids = {
                (data_set.__class__, data_set.id) for data_set in reference_data_sets
            }
            assert len(unique_ids) == len(reference_data_sets), (
                "multiple reference data sets of the same "
                "type and with the same id were provided"
            )

    @classmethod
    def generate(
        cls,
        model: T,
        conda_environment: str,
        max_time: str,
        evaluator_preset: str,
        evaluator_port: int,
        n_evaluator_workers: int,
        include_results: bool = False,
        reference_data_sets: Optional[List[Union[DataSet, QCDataSet]]] = None,
        optimization_result: Optional[OptimizationResult] = None,
    ):
        """Generates the required directory structure and inputs for the model.

        Parameters
        ----------
        model
            The model to generate the inputs for.
        conda_environment
            The name of the conda environment to run within.
        max_time
            The maximum wall-clock time for job submissions.
        evaluator_preset
            The present evaluator compute settings to use.
        evaluator_port
            The port to run the evaluator server on.
        n_evaluator_workers
            The target number of evaluator compute workers to spawn.
        include_results
            Whether to also download any previously generated results
            and store them alongside the inputs.
        reference_data_sets
            The reference data sets referenced by the model
        optimization_result
            The result of the optimization (if any) referenced by the model.
        """

        if not isinstance(model, (Benchmark, Optimization)) and (
            reference_data_sets is not None or optimization_result is not None
        ):

            raise NotImplementedError(
                "The `reference_data_sets` and `optimization_result` can currently "
                "only be provided when generating inputs for a benchmark or "
                "optimization directly."
            )

        os.makedirs(model.id, exist_ok=True)

        with temporary_cd(model.id):

            cls._generate(
                model,
                conda_environment,
                max_time,
                evaluator_preset,
                evaluator_port,
                n_evaluator_workers,
                include_results,
                reference_data_sets,
                optimization_result,
            )

            for child, factory in cls._yield_child_factory(model):
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

                    factory.generate(
                        model=child,
                        conda_environment=conda_environment,
                        max_time=max_time,
                        evaluator_preset=evaluator_preset,
                        evaluator_port=evaluator_port,
                        n_evaluator_workers=n_evaluator_workers,
                        include_results=include_results,
                        reference_data_sets=reference_data_sets,
                        optimization_result=optimization_result,
                    )
