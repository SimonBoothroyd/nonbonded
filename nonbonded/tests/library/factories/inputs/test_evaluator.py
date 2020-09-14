from openff.evaluator import backends, server
from openff.evaluator.backends import dask

from nonbonded.library.factories.inputs.evaluator import (
    ComputeResources,
    DaskHPCClusterConfig,
    DaskLocalClusterConfig,
    EvaluatorServerConfig,
    QueueWorkerResources,
)
from nonbonded.library.utilities import temporary_cd


def compare_compute_resources(
    compute_resources: ComputeResources,
    off_compute_resources: backends.ComputeResources,
):
    assert compute_resources.n_processes == off_compute_resources.number_of_threads
    assert compute_resources.n_gpus == off_compute_resources.number_of_gpus


def compare_queue_worker_resources(
    compute_resources: QueueWorkerResources,
    off_compute_resources: backends.QueueWorkerResources,
):
    compare_compute_resources(compute_resources, off_compute_resources)

    assert (
        compute_resources.wallclock_time_limit
        == off_compute_resources.wallclock_time_limit
    )
    assert (
        compute_resources.memory_limit
        == off_compute_resources.per_thread_memory_limit.magnitude
    )


def test_compute_resources_to_evaluator():
    compute_resources = ComputeResources()
    off_compute_resources = compute_resources.to_evaluator()

    compare_compute_resources(compute_resources, off_compute_resources)


def test_queue_resources_to_evaluator():

    compute_resources = QueueWorkerResources()
    off_compute_resources = compute_resources.to_evaluator()

    compare_compute_resources(compute_resources, off_compute_resources)


def test_dask_hpc_to_evaluator():

    config = DaskHPCClusterConfig(
        resources_per_worker=QueueWorkerResources(),
        queue_name="default",
        setup_script_commands=["pwd"],
    )

    assert config.to_evaluator() is not None


def test_dask_local_to_evaluator(monkeypatch):

    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")

    config = DaskLocalClusterConfig(
        number_of_workers=1, resources_per_worker=ComputeResources()
    )

    assert config.to_evaluator() is not None


def test_server_config_to_evaluator():

    server_config = EvaluatorServerConfig(
        backend_config=DaskLocalClusterConfig(
            resources_per_worker=ComputeResources(n_gpus=0)
        )
    )

    backend = server_config.to_backend()
    backend._started = True

    with temporary_cd():
        assert isinstance(backend, dask.DaskLocalCluster)
        assert isinstance(server_config.to_server(backend), server.EvaluatorServer)
