import logging
import os

from nonbonded.library.factories.analysis import AnalysisFactory
from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.models.projects import Benchmark
from nonbonded.library.models.results import BenchmarkResult
from nonbonded.library.utilities.migration import reindex_results
from nonbonded.library.utilities.provenance import summarise_current_versions

logger = logging.getLogger(__name__)


class BenchmarkAnalysisFactory(AnalysisFactory):
    @classmethod
    def analyze(cls, reindex):

        from openff.evaluator.client import RequestResult

        # Load in the definition of the benchmark to optimize.
        benchmark = Benchmark.parse_file("benchmark.json")

        # Create a directory to store the results in
        output_directory = "analysis"
        os.makedirs(output_directory, exist_ok=True)

        # Load the reference data set
        reference_data_sets = DataSetCollection.parse_file("test-set-collection.json")

        # Load in the request results.
        request_results: RequestResult = RequestResult.from_json("results.json")

        if reindex:
            request_results = reindex_results(request_results, reference_data_sets)

        if len(request_results.unsuccessful_properties) > 0:

            logger.warning(
                f"{len(request_results.unsuccessful_properties)} properties could "
                f"not be estimated and so were not analyzed:"
            )

            for unsuccessful_property in request_results.unsuccessful_properties:
                logger.warning(f"{unsuccessful_property.id} could not be estimated.")

        estimated_data_set = request_results.estimated_properties

        # Generate statistics for the estimated properties.
        benchmark_results = BenchmarkResult.from_evaluator(
            project_id=benchmark.project_id,
            study_id=benchmark.study_id,
            benchmark_id=benchmark.id,
            reference_data_set=reference_data_sets,
            estimated_data_set=estimated_data_set,
            analysis_environments=benchmark.analysis_environments,
        )
        benchmark_results.calculation_environment = cls._parse_calculation_environment()
        benchmark_results.analysis_environment = summarise_current_versions()

        # Save the results
        with open(
            os.path.join(output_directory, "benchmark-results.json"), "w"
        ) as file:
            file.write(benchmark_results.json())
