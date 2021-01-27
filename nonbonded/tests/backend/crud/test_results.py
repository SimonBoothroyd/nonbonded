import functools
from typing import List

import pytest
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.datasets import DataSetCRUD
from nonbonded.backend.database.crud.projects import BenchmarkCRUD, OptimizationCRUD
from nonbonded.backend.database.crud.results import (
    BenchmarkResultCRUD,
    OptimizationResultCRUD,
)
from nonbonded.backend.database.utilities.exceptions import (
    BenchmarkNotFoundError,
    BenchmarkResultExistsError,
    BenchmarkResultNotFoundError,
    DataSetEntryNotFound,
    ForceFieldExistsError,
    OptimizationNotFoundError,
    OptimizationResultExistsError,
    OptimizationResultNotFoundError,
    TargetNotFoundError,
    TargetResultNotFoundError,
    TargetResultTypeError,
    UnableToDeleteError,
    UnableToUpdateError,
)
from nonbonded.library.models.forcefield import ForceField
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import (
    DataSetResult,
    DataSetResultEntry,
    DataSetStatistic,
    EvaluatorTargetResult,
    RechargeTargetResult,
)
from nonbonded.library.statistics.statistics import StatisticType
from nonbonded.tests.backend.crud.utilities import BaseCRUDTest, create_dependencies
from nonbonded.tests.utilities.comparison import compare_pydantic_models, does_not_raise
from nonbonded.tests.utilities.factory import (
    create_benchmark,
    create_benchmark_result,
    create_data_set,
    create_data_set_statistic,
    create_evaluator_target,
    create_force_field,
    create_optimization,
    create_optimization_result,
    create_statistic,
)


def optimization_result_perturbations():

    return [
        ({"calculation_environment": {}}, lambda db: [], does_not_raise()),
        ({"analysis_environment": {}}, lambda db: [], does_not_raise()),
        (
            {"refit_force_field": ForceField(inner_content="update-ff")},
            lambda db: [],
            does_not_raise(),
        ),
        # Test updating the test_sets.
        (
            {
                "target_results": {
                    0: {
                        "evaluator-target-1": EvaluatorTargetResult(
                            objective_function=1.0,
                            statistic_entries=[create_data_set_statistic()],
                        ),
                        "recharge-target-1": RechargeTargetResult(
                            objective_function=0.5,
                            statistic_entries=[create_statistic()],
                        ),
                    },
                }
            },
            lambda db: [
                db.query(models.DataSetStatistic.id).count() == 1,
                db.query(models.DataSetResult.id).count() == 1,
                db.query(models.QCDataSetStatistic.id).count() == 1,
                db.query(models.QCDataSetResult.id).count() == 1,
                db.query(models.TargetResult.id).count() == 2,
                db.query(models.EvaluatorTargetResult.id).count() == 1,
                db.query(models.RechargeTargetResult.id).count() == 1,
            ],
            does_not_raise(),
        ),
    ]


def benchmark_result_perturbations():

    return [
        ({"calculation_environment": {}}, lambda db: [], does_not_raise()),
        ({"analysis_environment": {}}, lambda db: [], does_not_raise()),
        # Test updating the test_sets.
        (
            {
                "data_set_result": DataSetResult(
                    result_entries=[
                        DataSetResultEntry(
                            reference_id=1,
                            estimated_value=5.0,
                            estimated_std_error=5.0,
                            categories=["a", "b"],
                        ),
                    ],
                    statistic_entries=[
                        DataSetStatistic(
                            statistic_type=StatisticType.RMSE,
                            value=0.0,
                            lower_95_ci=0.0,
                            upper_95_ci=0.0,
                            category="a",
                            property_type="Density",
                            n_components=1,
                        )
                    ],
                )
            },
            lambda db: [
                db.query(models.DataSetStatistic.id).count() == 1,
                db.query(models.DataSetResult.id).count() == 1,
            ],
            does_not_raise(),
        ),
    ]


class TestOptimizationResultCRUD(BaseCRUDTest):
    @classmethod
    def crud_class(cls):
        return OptimizationResultCRUD

    @classmethod
    def dependencies(cls):
        return [
            "project",
            "study",
            "evaluator-target",
            "recharge-target",
            "data-set",
            "qc-data-set",
        ]

    @classmethod
    def create_model(cls, include_children=False, index=1):

        results = create_optimization_result(
            "project-1",
            "study-1",
            f"optimization-{index}",
            ["evaluator-target-1"],
            ["recharge-target-1"],
        )

        return results

    @classmethod
    def model_to_read_kwargs(cls, model):
        return {
            "project_id": model.project_id,
            "study_id": model.study_id,
            "sub_study_id": model.id,
        }

    @classmethod
    def model_to_read_all_kwargs(cls, model):
        return {}

    @classmethod
    def not_found_error(cls):
        return OptimizationResultNotFoundError

    @classmethod
    def already_exists_error(cls):
        return OptimizationResultExistsError

    @classmethod
    def check_has_deleted(cls, db: Session):

        assert db.query(models.Statistic.id).count() == 0

        assert db.query(models.DataSetStatistic.id).count() == 0
        assert db.query(models.DataSetResultEntry.id).count() == 0
        assert db.query(models.DataSetResult.id).count() == 0

        assert db.query(models.QCDataSetStatistic.id).count() == 0
        assert db.query(models.QCDataSetResult.id).count() == 0

        assert db.query(models.TargetResult.id).count() == 0
        assert db.query(models.EvaluatorTargetResult.id).count() == 0
        assert db.query(models.RechargeTargetResult.id).count() == 0

        assert db.query(models.OptimizationResult.id).count() == 0

        assert db.query(models.ForceField.id).count() == 1

        # Make sure the right force field as deleted
        remaining_force_field = db.query(models.ForceField.inner_content).first()
        assert "Refit" not in remaining_force_field

    @pytest.mark.parametrize(
        "perturbation, database_checks, expected_raise",
        optimization_result_perturbations(),
    )
    def test_update(self, db: Session, perturbation, database_checks, expected_raise):
        super(TestOptimizationResultCRUD, self).test_update(
            db, perturbation, database_checks, expected_raise
        )

    @pytest.mark.parametrize(
        "create_dependant_child, delete_dependant_child",
        [
            (
                functools.partial(
                    BenchmarkCRUD.create,
                    sub_study=create_benchmark(
                        "project-1",
                        "study-1",
                        "benchmark-1",
                        ["data-set-1"],
                        "optimization-1",
                        None,
                    ),
                ),
                functools.partial(
                    BenchmarkCRUD.delete,
                    project_id="project-1",
                    study_id="study-1",
                    sub_study_id="benchmark-1",
                ),
            ),
            (
                functools.partial(
                    OptimizationCRUD.create,
                    sub_study=Optimization(
                        **create_optimization(
                            "project-1",
                            "study-1",
                            "optimization-2",
                            [
                                create_evaluator_target(
                                    "evaluator-target-1", ["data-set-1"]
                                )
                            ],
                        ).dict(exclude={"force_field", "optimization_id"}),
                        optimization_id="optimization-1",
                    ),
                ),
                functools.partial(
                    OptimizationCRUD.delete,
                    project_id="project-1",
                    study_id="study-1",
                    sub_study_id="optimization-2",
                ),
            ),
        ],
    )
    def test_update_with_child(
        self, db: Session, create_dependant_child, delete_dependant_child
    ):
        """Test that optimization results which are being targeted by a benchmark
        / other optimization can only be updated if the refit force field does not
         change.
        """

        create_dependencies(db, self.dependencies())
        model = self.create_model()

        db.add(self.crud_class().create(db, model))
        db.commit()

        db.add(create_dependant_child(db))
        db.commit()

        # We should be able to update without changing the force field.
        db.begin_nested()
        self.crud_class().update(db, model)
        db.rollback()

        model.refit_force_field.inner_content += " refit"

        db.begin_nested()

        with pytest.raises(UnableToUpdateError):
            self.crud_class().update(db, model)

        db.rollback()

        # Delete the benchmark and results and try again.
        delete_dependant_child(db)
        db.commit()
        db_updated_result = self.crud_class().update(db, model)
        db.commit()

        compare_pydantic_models(self.crud_class().db_to_model(db_updated_result), model)

    @pytest.mark.skip("Optimization results cannot be paginated.")
    def test_pagination(self, db: Session):
        pass

    @pytest.mark.parametrize(
        "dependencies, expected_error",
        [
            (["evaluator-target", "recharge-target"], OptimizationNotFoundError),
            (["evaluator-target"], TargetNotFoundError),
            (["recharge-target"], TargetNotFoundError),
        ],
    )
    def test_missing_dependencies(
        self, db: Session, dependencies: List[str], expected_error
    ):
        super(TestOptimizationResultCRUD, self).test_missing_dependencies(
            db, dependencies, expected_error
        )

    @pytest.mark.parametrize(
        "recharge_target_ids, evaluator_target_ids, expected_target_ids",
        [
            ([], ["evaluator-target-1"], {"recharge-target-1"}),
            (["recharge-target-1"], [], {"evaluator-target-1"}),
        ],
    )
    def test_missing_target_result(
        self,
        db: Session,
        recharge_target_ids,
        evaluator_target_ids,
        expected_target_ids,
    ):
        """Tests that an exception is raised when results are uploaded but
        do not contain results for all of the expected targets."""

        create_dependencies(db, self.dependencies())

        model = create_optimization_result(
            "project-1",
            "study-1",
            "optimization-1",
            evaluator_target_ids,
            recharge_target_ids,
        )

        with pytest.raises(TargetResultNotFoundError) as error_info:
            self.crud_class().create(db, model)

        assert error_info.value.target_ids == expected_target_ids

    def test_invalid_target_result_type(self, db: Session):
        """Tests that an exception is raised when results are uploaded but
        do not contain results for all of the expected targets."""

        create_dependencies(db, self.dependencies())
        model = self.create_model(True)

        evaluator_results = model.target_results[0]["evaluator-target-1"]
        recharge_results = model.target_results[0]["recharge-target-1"]

        model.target_results = {
            0: {
                "evaluator-target-1": recharge_results,
                "recharge-target-1": evaluator_results,
            }
        }

        with pytest.raises(TargetResultTypeError):
            self.crud_class().create(db, model)

    @pytest.mark.skip("This case is handled by ``test_delete_with_child``.")
    def test_delete_with_dependent(
        self, db: Session, create_dependant, delete_dependant
    ):
        pass

    def test_duplicate_refit_force_field(self, db: Session):
        """Test that an exception is raised when uploading a refit
        force field when that force field already is present.
        """
        create_dependencies(db, self.dependencies())

        result = self.create_model()
        result.refit_force_field = create_force_field()

        # Make sure results with duplicate parents cannot be added.
        with pytest.raises(ForceFieldExistsError):
            OptimizationResultCRUD.create(db, result)

    @pytest.mark.parametrize(
        "create_dependant_child, delete_dependant_child",
        [
            (
                functools.partial(
                    BenchmarkCRUD.create,
                    sub_study=create_benchmark(
                        "project-1",
                        "study-1",
                        "benchmark-1",
                        ["data-set-1"],
                        "optimization-1",
                        None,
                    ),
                ),
                functools.partial(
                    BenchmarkCRUD.delete,
                    project_id="project-1",
                    study_id="study-1",
                    sub_study_id="benchmark-1",
                ),
            ),
            (
                functools.partial(
                    OptimizationCRUD.create,
                    sub_study=Optimization(
                        **create_optimization(
                            "project-1",
                            "study-1",
                            "optimization-2",
                            [
                                create_evaluator_target(
                                    "evaluator-target-1", ["data-set-1"]
                                )
                            ],
                        ).dict(exclude={"force_field", "optimization_id"}),
                        optimization_id="optimization-1",
                    ),
                ),
                functools.partial(
                    OptimizationCRUD.delete,
                    project_id="project-1",
                    study_id="study-1",
                    sub_study_id="optimization-2",
                ),
            ),
        ],
    )
    def test_delete_with_child(
        self, db: Session, create_dependant_child, delete_dependant_child
    ):
        """Test that optimization results which are being targeted by a benchmark
        can only be deleted once the benchmark has been deleted.
        """

        create_dependencies(db, self.dependencies())
        model = self.create_model()

        db.add(self.crud_class().create(db, model))
        db.commit()

        db.add(create_dependant_child(db))
        db.commit()

        db.begin_nested()

        with pytest.raises(UnableToDeleteError):
            self.crud_class().delete(db, model.project_id, model.study_id, model.id)

        db.rollback()

        # Delete the benchmark and results and try again.
        delete_dependant_child(db)
        db.commit()
        self.crud_class().delete(db, model.project_id, model.study_id, model.id)
        db.commit()

        self.check_has_deleted(db)


class TestBenchmarkResultCRUD(BaseCRUDTest):
    @classmethod
    def crud_class(cls):
        return BenchmarkResultCRUD

    @classmethod
    def dependencies(cls):
        return [
            "project",
            "study",
            "evaluator-target",
            "data-set",
            "benchmark",
        ]

    @classmethod
    def create_model(cls, include_children=False, index=1):

        data_set = create_data_set("data-set-1")
        data_set.entries[0].id = 1

        results = create_benchmark_result(
            "project-1", "study-1", f"benchmark-{index}", data_set
        )

        return results

    @classmethod
    def model_to_read_kwargs(cls, model):
        return {
            "project_id": model.project_id,
            "study_id": model.study_id,
            "sub_study_id": model.id,
        }

    @classmethod
    def model_to_read_all_kwargs(cls, model):
        return {}

    @classmethod
    def not_found_error(cls):
        return BenchmarkResultNotFoundError

    @classmethod
    def already_exists_error(cls):
        return BenchmarkResultExistsError

    @classmethod
    def check_has_deleted(cls, db: Session):

        assert db.query(models.Statistic.id).count() == 0

        assert db.query(models.DataSetStatistic.id).count() == 0
        assert db.query(models.DataSetResultEntry.id).count() == 0
        assert db.query(models.DataSetResult.id).count() == 0

        assert db.query(models.BenchmarkResult.id).count() == 0

    @pytest.mark.parametrize(
        "perturbation, database_checks, expected_raise",
        benchmark_result_perturbations(),
    )
    def test_update(self, db: Session, perturbation, database_checks, expected_raise):
        super(TestBenchmarkResultCRUD, self).test_update(
            db, perturbation, database_checks, expected_raise
        )

    @pytest.mark.skip("Benchmark results cannot be paginated.")
    def test_pagination(self, db: Session):
        pass

    @pytest.mark.parametrize(
        "dependencies, expected_error", [(["benchmark"], BenchmarkNotFoundError)]
    )
    def test_missing_dependencies(
        self, db: Session, dependencies: List[str], expected_error
    ):
        super(TestBenchmarkResultCRUD, self).test_missing_dependencies(
            db, dependencies, expected_error
        )

    @pytest.mark.skip("Benchmark results do not have dependants.")
    def test_delete_with_dependent(
        self, db: Session, create_dependant, delete_dependant
    ):
        pass

    def test_read_multiple_results(self, db: Session):
        """Test that a set benchmark results are correctly read when multiple
        sets of results are present.
        """

        n_results = 3

        create_dependencies(db, ["project", "study"])

        data_sets = []

        for index in range(n_results):

            db_data_set = DataSetCRUD.create(
                db, create_data_set(f"data-set-{index + 1}")
            )
            db.add(db_data_set)
            db.commit()

            data_sets.append(DataSetCRUD.db_to_model(db_data_set))

        # Add two new benchmarks
        for index in range(n_results):
            db.add(
                BenchmarkCRUD.create(
                    db,
                    create_benchmark(
                        "project-1",
                        "study-1",
                        f"benchmark-{index + 1}",
                        [f"data-set-{index + 1}"],
                        None,
                        create_force_field(),
                    ),
                )
            )

        db.commit()

        # Commit results for the benchmarks in reverse order as a more
        # comprehensive test.
        for index in reversed(range(n_results)):

            result = create_benchmark_result(
                "project-1", "study-1", f"benchmark-{index + 1}", data_sets[index]
            )

            db.add(BenchmarkResultCRUD.create(db, result))

        db.commit()

        for index in range(n_results):

            result = BenchmarkResultCRUD.read(
                db, "project-1", "study-1", f"benchmark-{index + 1}"
            )
            assert len(result.data_set_result.result_entries) == 1
            assert result.data_set_result.result_entries[0].reference_id == index + 1

    def test_missing_data_entry(self, db: Session):
        """Test that an exception is raised when the benchmark reports a result
        for a non-existent data entry.
        """

        create_dependencies(db, ["benchmark", "data-set"])
        data_set = create_data_set("data-set-1")
        data_set.entries[0].id = 1

        result = create_benchmark_result(
            "project-1", "study-1", "benchmark-1", data_set
        )

        for results_entry in result.data_set_result.result_entries:
            results_entry.reference_id = -1

        with pytest.raises(DataSetEntryNotFound):
            BenchmarkResultCRUD.create(db, result)
