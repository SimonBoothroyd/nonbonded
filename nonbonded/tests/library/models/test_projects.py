import pytest
from pydantic import ValidationError

from nonbonded.library.models.authors import Author
from nonbonded.library.models.engines import ForceBalance
from nonbonded.library.models.exceptions.exceptions import (
    DuplicateItemsError,
    MutuallyExclusiveError,
)
from nonbonded.library.models.forcefield import ForceField, Parameter
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study
from nonbonded.tests.utilities.factory import (
    create_evaluator_target,
    create_force_field,
    create_recharge_target,
)


@pytest.fixture(scope="module")
def valid_sub_study_kwargs():
    return {
        "id": "id",
        "study_id": "id",
        "project_id": "id",
        "name": "name",
        "description": "description",
    }


@pytest.fixture(scope="module")
def valid_optimization_kwargs(valid_sub_study_kwargs):

    force_field = ForceField(inner_content=" ")
    parameters = [Parameter(handler_type=" ", smirks=" ", attribute_name=" ")]

    return {
        **valid_sub_study_kwargs,
        "max_iterations": 1,
        "engine": ForceBalance(priors={" ": 1.0}),
        "targets": [
            create_evaluator_target("evaluator-target", ["data-set-1"]),
            create_recharge_target("recharge-target", ["qc-data-set-1"]),
        ],
        "force_field": force_field,
        "parameters_to_train": parameters,
        "analysis_environments": [],
    }


@pytest.fixture(scope="module")
def valid_benchmark_kwargs(valid_sub_study_kwargs):

    return {
        **valid_sub_study_kwargs,
        "test_set_ids": ["data-set-1"],
        "analysis_environments": [],
        "optimization_id": None,
        "force_field": create_force_field(),
    }


def test_optimization_target_validation(valid_optimization_kwargs):
    """Test that pydantic correctly validates optimization targets"""

    Optimization(**valid_optimization_kwargs)

    with pytest.raises(ValidationError):
        # The targets list cannot be empty.
        Optimization(**{**valid_optimization_kwargs, "targets": []})

    with pytest.raises(ValidationError):
        # The targets must have unique names.
        evaluator_target = create_evaluator_target("evaluator-target", ["data-set-1"])

        Optimization(
            **{
                **valid_optimization_kwargs,
                "targets": [evaluator_target, evaluator_target],
            }
        )

    with pytest.raises(ValidationError):
        # The list a parameters to optimizations cannot be empty.
        Optimization(**{**valid_optimization_kwargs, "parameters_to_train": []})

    with pytest.raises(ValidationError) as error_info:
        Optimization(
            **{
                **valid_optimization_kwargs,
                "parameters_to_train": [
                    Parameter(
                        handler_type="vdW", smirks="[#6X4:1]", attribute_name="epsilon"
                    )
                ]
                * 2,
            }
        )

    duplicate_error = error_info.value.raw_errors[0].exc
    assert isinstance(duplicate_error, DuplicateItemsError)

    assert len(duplicate_error.duplicate_items) == 1
    assert duplicate_error.field_name == "parameters_to_train"


def test_optimization_self_reference(valid_optimization_kwargs):

    # Create models which shouldn't raise exceptions
    with pytest.raises(ValidationError):
        Optimization(
            **{
                **valid_optimization_kwargs,
                "optimization_id": valid_optimization_kwargs["id"],
                "force_field": None,
            }
        )


@pytest.mark.parametrize("sub_study_class", [Optimization, Benchmark])
def test_mutually_exclusive_force_field(
    sub_study_class, valid_optimization_kwargs, valid_benchmark_kwargs
):

    valid_kwargs = (
        valid_optimization_kwargs
        if sub_study_class == Optimization
        else valid_benchmark_kwargs
    )

    # Create models which shouldn't raise exceptions
    sub_study_class(
        **{
            **valid_kwargs,
            "optimization_id": "optimization-2",
            "force_field": None,
        }
    )
    sub_study_class(
        **{
            **valid_kwargs,
            "optimization_id": None,
            "force_field": create_force_field(),
        }
    )

    # Test mutually exclusive fields.
    with pytest.raises(ValidationError) as error_info:
        sub_study_class(
            **{**valid_kwargs, "optimization_id": None, "force_field": None}
        )

    assert isinstance(error_info.value.raw_errors[0].exc, MutuallyExclusiveError)

    with pytest.raises(ValidationError) as error_info:
        sub_study_class(
            **{
                **valid_kwargs,
                "optimization_id": "optimization-2",
                "force_field": create_force_field(),
            }
        )

    assert isinstance(error_info.value.raw_errors[0].exc, MutuallyExclusiveError)


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
