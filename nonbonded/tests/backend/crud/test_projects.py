import functools
from typing import List

import pytest
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.projects import (
    BenchmarkCRUD,
    OptimizationCRUD,
    ProjectCRUD,
    StudyCRUD,
)
from nonbonded.backend.database.crud.results import (
    BenchmarkResultCRUD,
    OptimizationResultCRUD,
)
from nonbonded.backend.database.models.projects import author_projects_table
from nonbonded.backend.database.utilities.exceptions import (
    BenchmarkExistsError,
    BenchmarkNotFoundError,
    DataSetNotFoundError,
    MoleculeSetNotFoundError,
    OptimizationExistsError,
    OptimizationNotFoundError,
    ProjectExistsError,
    ProjectNotFoundError,
    StudyExistsError,
    StudyNotFoundError,
    UnableToCreateError,
    UnableToDeleteError,
    UnableToUpdateError,
)
from nonbonded.library.models.engines import ForceBalance
from nonbonded.library.models.forcefield import Parameter
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.targets import EvaluatorTarget, RechargeTarget
from nonbonded.library.utilities.environments import ChemicalEnvironment
from nonbonded.tests.backend.crud.utilities import (
    BaseCRUDTest,
    create_dependencies,
    update_and_compare_model,
)
from nonbonded.tests.utilities.comparison import does_not_raise
from nonbonded.tests.utilities.factory import (
    create_author,
    create_benchmark,
    create_benchmark_result,
    create_data_set,
    create_evaluator_target,
    create_force_field,
    create_optimization,
    create_optimization_result,
    create_project,
    create_recharge_target,
    create_study,
)


def project_model_perturbations():

    updated_author = create_author()
    updated_author.email = "updated@email.com"

    updated_study = create_study("project-1", "study-1")
    updated_study.name = "updated"

    return [
        ({"name": "updated"}, lambda db: [], does_not_raise()),
        ({"description": "updated"}, lambda db: [], does_not_raise()),
        (
            {"authors": [create_author(), updated_author]},
            lambda db: [
                db.query(models.Author.email).count() == 2,
                db.query(author_projects_table).count() == 2,
            ],
            does_not_raise(),
        ),
        # Delete a study.
        (
            {"studies": [create_study("project-1", "study-1")]},
            lambda db: [db.query(models.Study.id).count() == 1],
            does_not_raise(),
        ),
        # Update a study.
        (
            {"studies": [updated_study, create_study("project-1", "study-2")]},
            lambda db: [db.query(models.Study.id).count() == 2],
            does_not_raise(),
        ),
        # Add a study.
        (
            {
                "studies": [
                    create_study("project-1", f"study-{index + 1}")
                    for index in range(3)
                ]
            },
            lambda db: [db.query(models.Study.id).count() == 3],
            does_not_raise(),
        ),
    ]


def study_model_perturbations():

    updated_optimization = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        [create_evaluator_target("evaluator-target-1", ["data-set-1"])],
    )
    updated_optimization.max_iterations += 1

    updated_benchmark = create_benchmark(
        "project-1",
        "study-1",
        "benchmark-1",
        ["data-set-1"],
        None,
        create_force_field(),
    )
    updated_benchmark.name = "updated"

    return [
        ({"name": "updated"}, lambda db: [], does_not_raise()),
        ({"description": "updated"}, lambda db: [], does_not_raise()),
        # Delete an optimization.
        (
            {"optimizations": []},
            lambda db: [db.query(models.Optimization.id).count() == 0],
            does_not_raise(),
        ),
        # Update an optimization.
        (
            {"optimizations": [updated_optimization]},
            lambda db: [db.query(models.Optimization.id).count() == 1],
            does_not_raise(),
        ),
        # Add an optimization.
        (
            {
                "optimizations": [
                    create_optimization(
                        "project-1",
                        "study-1",
                        f"optimization-{index + 1}",
                        [create_evaluator_target("evaluator-target-1", ["data-set-1"])],
                    )
                    for index in range(2)
                ]
            },
            lambda db: [db.query(models.Optimization.id).count() == 2],
            does_not_raise(),
        ),
        # Delete a benchmark.
        (
            {"benchmarks": []},
            lambda db: [db.query(models.Benchmark.id).count() == 0],
            does_not_raise(),
        ),
        # Update a benchmark.
        (
            {"benchmarks": [updated_benchmark]},
            lambda db: [db.query(models.Benchmark.id).count() == 1],
            does_not_raise(),
        ),
        # Add a benchmark.
        (
            {
                "benchmarks": [
                    create_benchmark(
                        "project-1",
                        "study-1",
                        f"benchmark-{index + 1}",
                        ["data-set-1"],
                        None,
                        create_force_field(),
                    )
                    for index in range(2)
                ]
            },
            lambda db: [db.query(models.Benchmark.id).count() == 2],
            does_not_raise(),
        ),
    ]


def optimization_model_perturbations():

    updated_engine_delete_prior = ForceBalance(priors={"vdW/Atom/epsilon": 0.1})
    updated_engine_update_prior = ForceBalance(
        priors={"vdW/Atom/epsilon": 0.2, "vdW/Atom/sigma": 2.0},
    )
    updated_engine_add_prior = ForceBalance(
        priors={"vdW/Atom/epsilon": 0.1, "vdW/Atom/sigma": 2.0, "vdW/Atom/r_min": 2.0},
    )

    invalid_evaluator_target = create_evaluator_target(
        "evaluator-target-1", ["data-set-999"]
    )
    invalid_recharge_target = create_recharge_target(
        "recharge-target-1", ["molecule-set-999"]
    )

    return [
        ({"name": "updated"}, lambda db: [], does_not_raise()),
        ({"description": "updated"}, lambda db: [], does_not_raise()),
        ({"max_iterations": 999}, lambda db: [], does_not_raise()),
        (
            {"analysis_environments": [ChemicalEnvironment.Hydroxy]},
            lambda db: [],
            does_not_raise(),
        ),
        # Test updating the force field.
        (
            {"force_field": create_force_field("updated")},
            lambda db: [
                "updated" in db.query(models.ForceField.inner_content).first()[0],
                db.query(models.ForceField.id).count() == 1,
            ],
            does_not_raise(),
        ),
        # Test updating the parameters to train.
        (
            {
                "parameters_to_train": [
                    Parameter(
                        handler_type="vdW", smirks="[#6:1]", attribute_name="epsilon"
                    ),
                ]
            },
            lambda db: [db.query(models.Parameter.id).count() == 1],
            does_not_raise(),
        ),
        (
            {
                "parameters_to_train": [
                    Parameter(
                        handler_type="vdW", smirks="[#6:1]", attribute_name="epsilon"
                    ),
                    Parameter(
                        handler_type="vdW", smirks="[#6:1]", attribute_name="sigma"
                    ),
                    Parameter(
                        handler_type="vdW", smirks="[#1:1]", attribute_name="sigma"
                    ),
                ]
            },
            lambda db: [db.query(models.Parameter.id).count() == 3],
            does_not_raise(),
        ),
        # Test updating an engine's priors
        (
            {"engine": updated_engine_delete_prior},
            lambda db: [db.query(models.ForceBalancePrior.id).count() == 1],
            does_not_raise(),
        ),
        (
            {"engine": updated_engine_update_prior},
            lambda db: [db.query(models.ForceBalancePrior.id).count() == 2],
            does_not_raise(),
        ),
        (
            {"engine": updated_engine_add_prior},
            lambda db: [db.query(models.ForceBalancePrior.id).count() == 3],
            does_not_raise(),
        ),
        # Test deleting a target
        (
            {
                "targets": [
                    create_evaluator_target("evaluator-target-1", ["data-set-1"])
                ]
            },
            lambda db: [
                db.query(models.EvaluatorTarget.id).count() == 1,
                db.query(models.RechargeTarget.id).count() == 0,
            ],
            does_not_raise(),
        ),
        (
            {
                "targets": [
                    create_recharge_target("recharge-target-1", ["molecule-set-1"])
                ]
            },
            lambda db: [
                db.query(models.EvaluatorTarget.id).count() == 0,
                db.query(models.RechargeTarget.id).count() == 1,
            ],
            does_not_raise(),
        ),
        # Test adding a target
        (
            {
                "targets": [
                    create_evaluator_target("evaluator-target-1", ["data-set-1"]),
                    create_evaluator_target("evaluator-target-2", ["data-set-1"]),
                    create_recharge_target("recharge-target-1", ["molecule-set-1"]),
                ]
            },
            lambda db: [
                db.query(models.EvaluatorTarget.id).count() == 2,
                db.query(models.RechargeTarget.id).count() == 1,
            ],
            does_not_raise(),
        ),
        (
            {
                "targets": [
                    create_evaluator_target("evaluator-target-1", ["data-set-1"]),
                    create_recharge_target("recharge-target-1", ["molecule-set-1"]),
                    create_recharge_target("recharge-target-2", ["molecule-set-1"]),
                ]
            },
            lambda db: [
                db.query(models.EvaluatorTarget.id).count() == 1,
                db.query(models.RechargeTarget.id).count() == 2,
            ],
            does_not_raise(),
        ),
        # Test invalidly updating a target's training set
        (
            {"targets": [invalid_evaluator_target]},
            lambda db: [],
            pytest.raises(DataSetNotFoundError),
        ),
        (
            {"targets": [invalid_recharge_target]},
            lambda db: [],
            pytest.raises(MoleculeSetNotFoundError),
        ),
    ]


def benchmark_model_perturbations():

    return [
        ({"name": "updated"}, lambda db: [], does_not_raise()),
        ({"description": "updated"}, lambda db: [], does_not_raise()),
        (
            {"analysis_environments": [ChemicalEnvironment.Hydroxy]},
            lambda db: [],
            does_not_raise(),
        ),
        # Test updating the test_sets.
        ({"test_set_ids": ["data-set-1"]}, lambda db: [], does_not_raise()),
        (
            {"test_set_ids": ["data-set-2"]},
            lambda db: [],
            pytest.raises(DataSetNotFoundError),
        ),
    ]


class TestProjectCRUD(BaseCRUDTest):
    @classmethod
    def crud_class(cls):
        return ProjectCRUD

    @classmethod
    def dependencies(cls):
        return []

    @classmethod
    def create_model(cls, include_children=False, index=1):

        project = create_project(f"project-{index}")

        if include_children:
            project.studies = [
                create_study(project.id, "study-1"),
                create_study(project.id, "study-2"),
            ]

        return project

    @classmethod
    def model_to_read_kwargs(cls, model):
        return {"project_id": model.id}

    @classmethod
    def model_to_read_all_kwargs(cls, model):
        return {}

    @classmethod
    def not_found_error(cls):
        return ProjectNotFoundError

    @classmethod
    def already_exists_error(cls):
        return ProjectExistsError

    @classmethod
    def check_has_deleted(cls, db: Session):

        from nonbonded.backend.database.models.projects import author_projects_table

        assert db.query(models.Project.id).count() == 0
        assert db.query(author_projects_table).count() == 0

    @pytest.mark.parametrize(
        "perturbation, database_checks, expected_raise", project_model_perturbations()
    )
    def test_update(self, db: Session, perturbation, database_checks, expected_raise):
        super(TestProjectCRUD, self).test_update(
            db, perturbation, database_checks, expected_raise
        )

    @pytest.mark.skip("Projects do not have any dependencies.")
    def test_missing_dependencies(
        self, db: Session, dependencies: List[str], expected_error
    ):
        pass

    @pytest.mark.skip("Projects do not directly have blocking dependants.")
    def test_delete_with_dependent(
        self, db: Session, create_dependant, delete_dependant
    ):
        pass


class TestStudyCRUD(BaseCRUDTest):
    @classmethod
    def crud_class(cls):
        return StudyCRUD

    @classmethod
    def dependencies(cls):
        return ["project", "data-set", "test-data-set"]

    @classmethod
    def create_model(cls, include_children=False, index=1):

        study = create_study("project-1", f"study-{index}")

        if include_children:

            study.optimizations = [
                create_optimization(
                    "project-1",
                    study.id,
                    "optimization-1",
                    [create_evaluator_target("evaluator-target-1", ["data-set-1"])],
                )
            ]
            study.benchmarks = [
                create_benchmark(
                    "project-1",
                    study.id,
                    "benchmark-1",
                    ["data-set-1"],
                    None,
                    create_force_field(),
                )
            ]

        return study

    @classmethod
    def model_to_read_kwargs(cls, model):
        return {"project_id": model.project_id, "study_id": model.id}

    @classmethod
    def model_to_read_all_kwargs(cls, model):
        return {"project_id": model.project_id}

    @classmethod
    def not_found_error(cls):
        return StudyNotFoundError

    @classmethod
    def already_exists_error(cls):
        return StudyExistsError

    @classmethod
    def check_has_deleted(cls, db: Session):

        assert db.query(models.Study.id).count() == 0
        assert len(db.query(models.Project).first().studies) == 0

        assert db.query(models.Optimization.id).count() == 0
        assert db.query(models.Benchmark.id).count() == 0

    @pytest.mark.parametrize(
        "perturbation, database_checks, expected_raise", study_model_perturbations()
    )
    def test_update(self, db: Session, perturbation, database_checks, expected_raise):
        super(TestStudyCRUD, self).test_update(
            db, perturbation, database_checks, expected_raise
        )

    @pytest.mark.parametrize(
        "dependencies, expected_error", [(["project"], ProjectNotFoundError)]
    )
    def test_missing_dependencies(
        self, db: Session, dependencies: List[str], expected_error
    ):
        super(TestStudyCRUD, self).test_missing_dependencies(
            db, dependencies, expected_error
        )

    @pytest.mark.skip("Studies do not directly have blocking dependants.")
    def test_delete_with_dependent(
        self, db: Session, create_dependant, delete_dependant
    ):
        pass


class TestOptimizationCRUD(BaseCRUDTest):
    @classmethod
    def crud_class(cls):
        return OptimizationCRUD

    @classmethod
    def dependencies(cls):
        return ["project", "study", "data-set", "molecule-set"]

    @classmethod
    def create_model(cls, include_children=False, index=1):

        optimization = create_optimization(
            "project-1",
            "study-1",
            f"optimization-{index}",
            targets=[
                create_evaluator_target("evaluator-target-1", ["data-set-1"]),
                create_recharge_target("recharge-target-1", ["molecule-set-1"]),
            ],
        )

        return optimization

    @classmethod
    def model_to_read_kwargs(cls, model):
        return {
            "project_id": model.project_id,
            "study_id": model.study_id,
            "sub_study_id": model.id,
        }

    @classmethod
    def model_to_read_all_kwargs(cls, model):
        return {"project_id": model.project_id, "study_id": model.study_id}

    @classmethod
    def not_found_error(cls):
        return OptimizationNotFoundError

    @classmethod
    def already_exists_error(cls):
        return OptimizationExistsError

    @classmethod
    def check_has_deleted(cls, db: Session):

        assert db.query(models.Optimization.id).count() == 0
        assert db.query(models.ForceField.id).count() == 0
        assert db.query(models.Parameter.id).count() == 0
        assert db.query(models.ForceBalance.id).count() == 0
        assert db.query(models.EvaluatorTarget.id).count() == 0
        assert db.query(models.RechargeTarget.id).count() == 0

        # These should not be deleted.
        assert db.query(models.DataSet.id).count() == 1
        assert db.query(models.MoleculeSet.id).count() == 1

    @pytest.mark.parametrize(
        "perturbation, database_checks, expected_raise",
        optimization_model_perturbations(),
    )
    def test_update(self, db: Session, perturbation, database_checks, expected_raise):
        super(TestOptimizationCRUD, self).test_update(
            db, perturbation, database_checks, expected_raise
        )

    @pytest.mark.parametrize(
        "dependencies, expected_error",
        [
            (["study"], StudyNotFoundError),
            (["data-set"], DataSetNotFoundError),
            (["molecule-set"], MoleculeSetNotFoundError),
        ],
    )
    def test_missing_dependencies(
        self, db: Session, dependencies: List[str], expected_error
    ):
        super(TestOptimizationCRUD, self).test_missing_dependencies(
            db, dependencies, expected_error
        )

    @pytest.mark.parametrize("with_children", [False, True])
    def test_update_delete_with_dependant(self, db: Session, with_children: bool):
        """Test that an optimization which has dependants can only be
        updated / deleted once the dependants have been deleted.
        """

        # Create the model.
        create_dependencies(db, self.dependencies())
        model = self.create_model(True)

        db_model = self.crud_class().create(db, model)
        db.add(db_model)
        db.commit()

        # Create the results
        db_result = OptimizationResultCRUD.create(
            db,
            create_optimization_result(
                model.project_id,
                model.study_id,
                model.id,
                [
                    target.id
                    for target in model.targets
                    if isinstance(target, EvaluatorTarget)
                ],
                [
                    target.id
                    for target in model.targets
                    if isinstance(target, RechargeTarget)
                ],
            ),
        )
        db.add(db_result)
        db.commit()

        if with_children:

            db_benchmark = BenchmarkCRUD.create(
                db,
                create_benchmark(
                    model.project_id,
                    model.study_id,
                    "benchmark-1",
                    ["data-set-1"],
                    model.id,
                    None,
                ),
            )
            db.add(db_benchmark)

            db_optimization = OptimizationCRUD.create(
                db,
                Optimization(
                    **create_optimization(
                        model.project_id,
                        model.study_id,
                        "optimization-2",
                        [create_evaluator_target("evaluator-target-1", ["data-set-1"])],
                    ).dict(exclude={"force_field", "optimization_id"}),
                    force_field=None,
                    optimization_id="optimization-1",
                ),
            )
            db.add(db_optimization)
            db.commit()

        error_matches = (
            ["results"] if not with_children else ["benchmark-1", "optimization-2"]
        )

        with pytest.raises(UnableToDeleteError) as error_info:
            OptimizationCRUD.delete(db, model.project_id, model.study_id, model.id)

        assert all(
            error_match in str(error_info.value) for error_match in error_matches
        )

        with pytest.raises(UnableToUpdateError) as error_info:
            OptimizationCRUD.update(db, model)

        assert all(
            error_match in str(error_info.value) for error_match in error_matches
        )

        # Delete the dependants and try again.
        if with_children:

            BenchmarkCRUD.delete(db, model.project_id, model.study_id, "benchmark-1")
            OptimizationCRUD.delete(
                db, model.project_id, model.study_id, "optimization-2"
            )

            db.commit()

        OptimizationResultCRUD.delete(db, model.project_id, model.study_id, model.id)
        db.commit()

        OptimizationCRUD.update(db, model)
        db.commit()
        OptimizationCRUD.delete(db, model.project_id, model.study_id, model.id)
        db.commit()

    @pytest.mark.skip("This case is handled by ``test_update_delete_with_dependant``.")
    def test_delete_with_dependent(
        self, db: Session, create_dependant, delete_dependant
    ):
        pass


class TestBenchmarkCRUD(BaseCRUDTest):
    @classmethod
    def crud_class(cls):
        return BenchmarkCRUD

    @classmethod
    def dependencies(cls):
        return [
            "project",
            "study",
            "evaluator-target",
            "data-set",
        ]

    @classmethod
    def create_model(cls, include_children=False, index=1):

        benchmark = create_benchmark(
            "project-1",
            "study-1",
            f"benchmark-{index}",
            ["data-set-1"],
            None,
            create_force_field(),
        )

        return benchmark

    @classmethod
    def model_to_read_kwargs(cls, model):
        return {
            "project_id": model.project_id,
            "study_id": model.study_id,
            "sub_study_id": model.id,
        }

    @classmethod
    def model_to_read_all_kwargs(cls, model):
        return {"project_id": model.project_id, "study_id": model.study_id}

    @classmethod
    def not_found_error(cls):
        return BenchmarkNotFoundError

    @classmethod
    def already_exists_error(cls):
        return BenchmarkExistsError

    @classmethod
    def check_has_deleted(cls, db: Session):

        assert db.query(models.Benchmark.id).count() == 0
        # assert db.query(models.ForceField.id).count() == 0

    @pytest.mark.parametrize(
        "perturbation, database_checks, expected_raise", benchmark_model_perturbations()
    )
    def test_update(self, db: Session, perturbation, database_checks, expected_raise):
        super(TestBenchmarkCRUD, self).test_update(
            db, perturbation, database_checks, expected_raise
        )

    @pytest.mark.parametrize(
        "dependencies, expected_error",
        [(["study", "evaluator-target"], StudyNotFoundError)],
    )
    def test_missing_dependencies(
        self, db: Session, dependencies: List[str], expected_error
    ):
        super(TestBenchmarkCRUD, self).test_missing_dependencies(
            db, dependencies, expected_error
        )

    @pytest.mark.parametrize(
        "optimization_id, create_results, expected_error",
        [
            ("optimization-2", True, pytest.raises(OptimizationNotFoundError)),
            ("optimization-1", True, does_not_raise()),
            ("optimization-1", False, pytest.raises(UnableToCreateError)),
        ],
    )
    def test_create_read_with_optimization(
        self, db: Session, optimization_id: str, create_results: bool, expected_error
    ):
        """Test that a benchmark can be successfully created and then
        retrieved out again while targeting an optimization, or raises
        the correct error when no results have been created..
        """

        create_dependencies(db, self.dependencies())

        model = self.create_model(True)
        model.force_field = None
        model.optimization_id = optimization_id

        # Create the optimization results
        if create_results:

            db_result = OptimizationResultCRUD.create(
                db,
                create_optimization_result(
                    model.project_id,
                    model.study_id,
                    "optimization-1",
                    ["evaluator-target-1"],
                    [],
                ),
            )
            db.add(db_result)
            db.commit()

        with expected_error:
            self.test_create_read(db, False, model)

    @pytest.mark.parametrize(
        "optimization_id, create_results, expected_error",
        [
            ("optimization-2", True, pytest.raises(OptimizationNotFoundError)),
            ("optimization-1", True, does_not_raise()),
            ("optimization-1", False, pytest.raises(UnableToUpdateError)),
        ],
    )
    def test_update_with_dependant(
        self, db: Session, optimization_id: str, create_results: bool, expected_error
    ):
        """Test that a benchmark can be updated to target an optimization
        and then back to a force field.
        """

        create_dependencies(db, self.dependencies())
        model = self.create_model()

        db.add(self.crud_class().create(db, model))
        db.commit()

        # Create the optimization results
        if create_results:
            db_result = OptimizationResultCRUD.create(
                db,
                create_optimization_result(
                    model.project_id,
                    model.study_id,
                    "optimization-1",
                    ["evaluator-target-1"],
                    [],
                ),
            )
            db.add(db_result)
            db.commit()

        # Update the model.
        model.force_field = None
        model.optimization_id = optimization_id

        with expected_error:

            update_and_compare_model(
                db,
                model,
                self.crud_class().update,
                functools.partial(
                    self.crud_class().read, **self.model_to_read_kwargs(model)
                ),
                self.crud_class().db_to_model,
            )

        # Neither the refit force field nor the initial force field
        # should be deleted.
        assert db.query(models.ForceField.id).count() == 2 if create_results else 1

        # Update the model back.
        model.force_field = create_force_field()
        model.optimization_id = None

        update_and_compare_model(
            db,
            model,
            self.crud_class().update,
            functools.partial(
                self.crud_class().read, **self.model_to_read_kwargs(model)
            ),
            self.crud_class().db_to_model,
        )

        assert db.query(models.ForceField.id).count() == 2 if create_results else 1

    @pytest.mark.parametrize(
        "create_results, expected_error",
        [(False, does_not_raise()), (True, pytest.raises(UnableToDeleteError))],
    )
    def test_delete_with_dependent(
        self, db: Session, create_results: bool, expected_error
    ):
        """Test that a benchmark cannot be deleted until its results have
        also been deleted.
        """

        create_dependencies(db, self.dependencies())
        model = self.create_model()

        db.add(self.crud_class().create(db, model))
        db.commit()

        # Create the benchmark results
        if create_results:

            data_set = create_data_set("data-set-1")
            data_set.entries[0].id = 1

            db_result = BenchmarkResultCRUD.create(
                db,
                create_benchmark_result(
                    model.project_id, model.study_id, model.id, data_set
                ),
            )
            db.add(db_result)
            db.commit()

        # Delete the model.
        with expected_error:
            self.crud_class().delete(db, model.project_id, model.study_id, model.id)

        if not create_results:
            return

        BenchmarkResultCRUD.delete(db, model.project_id, model.study_id, model.id)
        db.commit()

        self.crud_class().delete(db, model.project_id, model.study_id, model.id)
        db.commit()

        self.check_has_deleted(db)
