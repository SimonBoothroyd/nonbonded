from nonbonded.library.config import settings
from nonbonded.library.models.datasets import DataSet, DataSetCollection
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study, \
    StudyCollection, ProjectCollection
from nonbonded.library.models.results import BenchmarkResult, OptimizationResult


def mock_get_data_set(requests_mock, data_set: DataSet):
    """Mock the get data sets endpoint."""
    requests_mock.get(
        DataSet._get_endpoint(data_set_id=data_set.id), text=data_set.json(),
    )


def mock_get_data_sets(requests_mock, data_sets: DataSetCollection):
    """Mock the get data sets endpoint."""
    requests_mock.get(
        f"{settings.API_URL}/datasets/", text=data_sets.json(),
    )


def mock_get_project(requests_mock, project: Project):
    """Mock the get project endpoint."""
    requests_mock.get(
        Project._get_endpoint(project_id=project.id), text=project.json(),
    )


def mock_get_projects(requests_mock, projects: ProjectCollection):
    """Mock the get projects endpoint."""
    requests_mock.get(
        f"{settings.API_URL}/projects/", text=projects.json(),
    )


def mock_get_study(requests_mock, study: Study):
    """Mock the get study endpoint."""
    requests_mock.get(
        Study._get_endpoint(project_id=study.project_id, study_id=study.id),
        text=study.json(),
    )


def mock_get_studies(requests_mock, project_id, studies: StudyCollection):
    """Mock the get studies endpoint."""
    requests_mock.get(
        f"{settings.API_URL}/projects/{project_id}/studies/", text=studies.json(),
    )


def mock_get_optimization(requests_mock, optimization: Optimization):
    """Mock the get optimization endpoint."""
    requests_mock.get(
        Optimization._get_endpoint(
            project_id=optimization.project_id,
            study_id=optimization.study_id,
            optimization_id=optimization.id,
        ),
        text=optimization.json(),
    )


def mock_get_optimization_result(
    requests_mock, optimization_result: OptimizationResult
):
    """Mock the get optimization result endpoint."""

    requests_mock.get(
        OptimizationResult._get_endpoint(
            project_id=optimization_result.project_id,
            study_id=optimization_result.study_id,
            model_id=optimization_result.id,
        ),
        text=optimization_result.json(),
    )


def mock_get_benchmark(requests_mock, benchmark: Benchmark):
    """Mock the get benchmark endpoint."""
    requests_mock.get(
        Benchmark._get_endpoint(
            project_id=benchmark.project_id,
            study_id=benchmark.study_id,
            benchmark_id=benchmark.id,
        ),
        text=benchmark.json(),
    )


def mock_get_benchmark_result(requests_mock, benchmark_result: BenchmarkResult):
    """Mock the get benchmark result endpoint."""

    requests_mock.get(
        BenchmarkResult._get_endpoint(
            project_id=benchmark_result.project_id,
            study_id=benchmark_result.study_id,
            model_id=benchmark_result.id,
        ),
        text=benchmark_result.json(),
    )
