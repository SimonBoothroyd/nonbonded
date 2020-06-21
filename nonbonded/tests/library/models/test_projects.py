import pytest
from pydantic import ValidationError

from nonbonded.library.models.authors import Author
from nonbonded.library.models.forcebalance import ForceBalanceOptions
from nonbonded.library.models.forcefield import ForceField, Parameter
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study


@pytest.fixture(scope="module")
def valid_optimization_kwargs():

    force_field = ForceField(inner_content=" ")
    parameters = [Parameter(handler_type=" ", smirks=" ", attribute_name=" ")]

    return {
        "id": "id",
        "study_id": "id",
        "project_id": "id",
        "name": " ",
        "description": " ",
        "training_set_ids": ["id"],
        "initial_force_field": force_field,
        "parameters_to_train": parameters,
        "force_balance_input": ForceBalanceOptions(),
        "denominators": {" ": " "},
        "priors": {" ": 1.0},
        "analysis_environments": [],
    }


@pytest.fixture(scope="module")
def valid_benchmark_kwargs():

    return {
        "id": "id",
        "study_id": "id",
        "project_id": "id",
        "name": " ",
        "description": " ",
        "test_set_ids": ["id"],
        "analysis_environments": [],
        "optimization_id": None,
        "force_field": ForceField(inner_content=" "),
    }


def test_optimization_validation(valid_optimization_kwargs):
    """Test that pydantic correctly validates optimizations"""

    Optimization(**valid_optimization_kwargs)

    with pytest.raises(ValidationError):
        # The list a training set ids cannot be empty.
        Optimization(**{**valid_optimization_kwargs, "training_set_ids": []})

    with pytest.raises(ValidationError):
        # The list a parameters to optimizations cannot be empty.
        Optimization(**{**valid_optimization_kwargs, "parameters_to_train": []})

    with pytest.raises(ValidationError):
        # Negative priors are not allowed.
        Optimization(**{**valid_optimization_kwargs, "priors": {" ": -1.0}})


def test_benchmark_validation(valid_benchmark_kwargs):
    """Test that pydantic correctly validates benchmarks"""

    Benchmark(**{**valid_benchmark_kwargs, "optimization_id": " ", "force_field": None})
    Benchmark(
        **{
            **valid_benchmark_kwargs,
            "optimization_id": None,
            "force_field": ForceField(inner_content=" "),
        }
    )

    # Test mutually exclusive fields.
    with pytest.raises(ValidationError):
        Benchmark(
            **{**valid_benchmark_kwargs, "optimization_id": None, "force_field": None}
        )
    with pytest.raises(ValidationError):
        Benchmark(
            **{
                **valid_benchmark_kwargs,
                "optimization_id": " ",
                "force_field": ForceField(inner_content=" "),
            }
        )


def test_study_validation(valid_optimization_kwargs, valid_benchmark_kwargs):
    """Test that pydantic correctly validates studies"""

    study_id = "study1"

    # Test that a valid study can be produced
    study_kwargs = {
        "id": study_id,
        "project_id": "a",
        "name": " ",
        "description": " ",
    }

    Study(
        **study_kwargs,
        optimizations=[
            Optimization(**{**valid_optimization_kwargs, "study_id": study_id})
        ],
        benchmarks=[Benchmark(**{**valid_benchmark_kwargs, "study_id": study_id})]
    )

    # Test non-unique ids.
    with pytest.raises(ValidationError):
        Study(
            **study_kwargs,
            optimizations=[
                Optimization(**{**valid_optimization_kwargs, "study_id": study_id}),
                Optimization(**{**valid_optimization_kwargs, "study_id": study_id}),
            ]
        )
    with pytest.raises(ValidationError):
        Study(
            **study_kwargs,
            benchmarks=[
                Benchmark(**{**valid_benchmark_kwargs, "study_id": study_id}),
                Benchmark(**{**valid_benchmark_kwargs, "study_id": study_id}),
            ]
        )

    # Test bad study id.
    with pytest.raises(ValidationError):

        Study(
            **study_kwargs,
            optimizations=[
                Optimization(**{**valid_optimization_kwargs, "study_id": " "})
            ]
        )

    with pytest.raises(ValidationError):
        Study(
            **study_kwargs,
            benchmarks=[Benchmark(**{**valid_benchmark_kwargs, "study_id": " "})]
        )

    # Test benchmark references an optimization which exists
    Study(
        **study_kwargs,
        optimizations=[
            Optimization(
                **{**valid_optimization_kwargs, "id": "optim1", "study_id": study_id}
            )
        ],
        benchmarks=[
            Benchmark(
                **{
                    **valid_benchmark_kwargs,
                    "study_id": study_id,
                    "optimization_id": "optim1",
                    "force_field": None,
                }
            )
        ]
    )

    with pytest.raises(ValidationError):
        Study(
            **study_kwargs,
            optimizations=[
                Optimization(
                    **{
                        **valid_optimization_kwargs,
                        "id": "optim1",
                        "study_id": study_id,
                    }
                )
            ],
            benchmarks=[
                Benchmark(
                    **{
                        **valid_benchmark_kwargs,
                        "study_id": study_id,
                        "optimization_id": "optim2",
                        "force_field": None,
                    }
                )
            ]
        )


def test_project_validation(valid_optimization_kwargs, valid_benchmark_kwargs):
    """Test that pydantic correctly validates studies"""

    project_id = "project-1"
    study_id = "study-1"

    # Test that a valid project can be produced
    project_kwargs = {
        "id": project_id,
        "name": " ",
        "description": " ",
        "authors": [Author(name=" ", email="x@x.com", institute=" ")],
    }

    valid_study = Study(
        id=study_id,
        project_id=project_id,
        name=" ",
        description=" ",
        optimizations=[
            Optimization(
                **{
                    **valid_optimization_kwargs,
                    "project_id": project_id,
                    "study_id": study_id,
                }
            )
        ],
        benchmarks=[
            Benchmark(
                **{
                    **valid_benchmark_kwargs,
                    "project_id": project_id,
                    "study_id": study_id,
                }
            )
        ],
    )

    Project(**project_kwargs, studies=[valid_study])

    # Test non-unique ids.
    with pytest.raises(ValidationError):
        Project(**project_kwargs, studies=[valid_study, valid_study])

    # Test bad project id.
    bad_study = Study(**{**valid_study.dict(), "project_id": "a"})

    with pytest.raises(ValidationError):
        Project(**project_kwargs, studies=[bad_study])

    bad_study = Study(**valid_study.dict())
    bad_study.optimizations[0].project_id = "a"

    with pytest.raises(ValidationError):
        Project(**project_kwargs, studies=[bad_study])

    bad_study = Study(**valid_study.dict())
    bad_study.benchmarks[0].project_id = "a"

    with pytest.raises(ValidationError):
        Project(**project_kwargs, studies=[bad_study])
