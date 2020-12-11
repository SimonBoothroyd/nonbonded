import abc
from typing import Any, Dict, Optional, Type, Union

from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.authors import AuthorCRUD
from nonbonded.backend.database.crud.datasets import DataSetCRUD
from nonbonded.backend.database.crud.forcefield import ForceFieldCRUD, ParameterCRUD
from nonbonded.backend.database.crud.targets import (
    EvaluatorTargetCRUD,
    RechargeTargetCRUD,
)
from nonbonded.backend.database.utilities.exceptions import (
    BenchmarkExistsError,
    BenchmarkNotFoundError,
    DataSetNotFoundError,
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
from nonbonded.library.models import projects
from nonbonded.library.models.engines import ForceBalance
from nonbonded.library.models.targets import EvaluatorTarget, RechargeTarget
from nonbonded.library.utilities.environments import ChemicalEnvironment


class SubStudyCRUD(abc.ABC):
    """A base class for optimization and benchmark CRUD methods."""

    @classmethod
    @abc.abstractmethod
    def orm_class(cls) -> Type[Union[models.Benchmark, models.Optimization]]:
        """Returns the ORM class associated with the CRUD."""

    @classmethod
    @abc.abstractmethod
    def rest_class(cls) -> Type[Union[projects.Benchmark, projects.Optimization]]:
        """Returns the REST class associated with the CRUD."""

    @classmethod
    @abc.abstractmethod
    def attribute_name(cls) -> str:
        """The attribute of the parent study which corresponds to the set of
        child sub-studies associated with this CRUD."""

    @classmethod
    @abc.abstractmethod
    def exists_error(
        cls,
    ) -> Union[Type[BenchmarkExistsError], Type[OptimizationExistsError]]:
        """The error to raise when attempting to add an entry which already exists in
        the database."""

    @classmethod
    @abc.abstractmethod
    def not_found_error(
        cls,
    ) -> Union[Type[BenchmarkNotFoundError], Type[OptimizationNotFoundError]]:
        """The error to raise when attempting to retrieve an entry which could not
        be found in the database."""

    @classmethod
    def query(
        cls, db: Session, project_id: str, study_id: str, sub_study_id: str
    ) -> models.SubStudy:

        db_benchmark = (
            db.query(cls.orm_class())
            .filter(cls.orm_class().identifier == sub_study_id)
            .join(models.Study)
            .filter(models.Study.identifier == study_id)
            .join(models.Project)
            .filter(models.Project.identifier == project_id)
            .first()
        )

        return db_benchmark

    @classmethod
    def _check_dependencies_exist(cls, db: Session, sub_study: projects.SubStudy):
        """"""

        # Check that any referenced optimization exists.
        if sub_study.optimization_id is None:
            return

        db_optimization = OptimizationCRUD.query(
            db, sub_study.project_id, sub_study.study_id, sub_study.optimization_id
        )

        if db_optimization is None:
            raise OptimizationNotFoundError(
                sub_study.project_id, sub_study.study_id, sub_study.optimization_id
            )

    @classmethod
    @abc.abstractmethod
    def _check_has_dependants(
        cls,
        db: Session,
        db_sub_study: models.Benchmark,
        error_type: Type[Union[UnableToUpdateError, UnableToDeleteError]],
    ):
        """A method to check whether all of the required dependencies (such as training
        or test sets) of a sub-study are present in the database, and which raises the
        correct exception if not."""

    @classmethod
    @abc.abstractmethod
    def _db_model_kwargs(
        cls,
        db: Session,
        sub_study,
        db_parent: models.Study,
        db_force_field: Optional[models.ForceField],
    ) -> Dict[str, Any]:
        """Returns the kwargs to create a new database model with."""

        return dict(
            identifier=sub_study.id,
            parent=db_parent,
            name=sub_study.name,
            description=sub_study.description,
            force_field=db_force_field,
            optimization=(
                None
                if sub_study.optimization_id is None
                else OptimizationCRUD.query(
                    db,
                    sub_study.project_id,
                    sub_study.study_id,
                    sub_study.optimization_id,
                )
            ),
            analysis_environments=[
                models.ChemicalEnvironment.unique(
                    db, models.ChemicalEnvironment(id=x.value)
                )
                for x in sub_study.analysis_environments
            ],
        )

    @classmethod
    def create(
        cls, db: Session, sub_study: projects.SubStudy, parent=None
    ) -> models.Benchmark:

        # Make sure a sub-study does not already exist with the new identifiers.
        if (
            cls.query(db, sub_study.project_id, sub_study.study_id, sub_study.id)
            is not None
        ):

            raise cls.exists_error()(
                sub_study.project_id, sub_study.study_id, sub_study.id
            )

        # Make sure all of the required dependencies exist in the data base.
        cls._check_dependencies_exist(db, sub_study)

        # Make sure the parent of the sub-study exists and retrieve it.
        if parent is None:
            parent = StudyCRUD.query(db, sub_study.project_id, sub_study.study_id)

        if parent is None:
            raise StudyNotFoundError(sub_study.project_id, sub_study.study_id)

        # noinspection PyArgumentList
        db_model = cls.orm_class()(
            **cls._db_model_kwargs(
                db=db,
                sub_study=sub_study,
                db_parent=parent,
                db_force_field=(
                    None
                    if sub_study.force_field is None
                    else models.ForceField.unique(
                        db,
                        models.ForceField(
                            inner_content=sub_study.force_field.inner_content
                        ),
                    )
                ),
            )
        )

        return db_model

    @classmethod
    def read_all(cls, db: Session, project_id: str, study_id: str):

        db_study = StudyCRUD.query(db, project_id=project_id, study_id=study_id)

        if not db_study:
            raise StudyNotFoundError(project_id, study_id)

        sub_studies = getattr(db_study, cls.attribute_name())

        return [cls.db_to_model(sub_study) for sub_study in sub_studies]

    @classmethod
    def read(cls, db: Session, project_id: str, study_id: str, sub_study_id: str):

        db_model = cls.query(db, project_id, study_id, sub_study_id)

        if not db_model:
            raise cls.not_found_error()(project_id, study_id, sub_study_id)

        return cls.db_to_model(db_model)

    @classmethod
    def update(cls, db: Session, sub_study: projects.SubStudy):

        db_sub_study = cls.query(
            db, sub_study.project_id, sub_study.study_id, sub_study.id
        )

        # Make sure the study to update exists.
        if not db_sub_study:

            raise cls.not_found_error()(
                sub_study.project_id, sub_study.study_id, sub_study.id
            )

        # Make sure this study is free to be updated and not locked by a
        # dependant.
        cls._check_has_dependants(db, db_sub_study, UnableToUpdateError)

        # Make sure that any of the newly required dependencies actually exist.
        cls._check_dependencies_exist(db, sub_study)

        db_sub_study.name = sub_study.name
        db_sub_study.description = sub_study.description

        original_force_field = db_sub_study.force_field

        db_sub_study.force_field = (
            None
            if sub_study.force_field is None
            else models.ForceField.unique(
                db, models.ForceField(inner_content=sub_study.force_field.inner_content)
            )
        )

        if (sub_study.force_field is None and original_force_field is not None) or (
            sub_study.force_field is not None
            and original_force_field is not None
            and original_force_field.inner_content
            != sub_study.force_field.inner_content
        ):
            # Attempt to delete the FF if it might now be an orphan.
            ForceFieldCRUD.delete(db, original_force_field)

        db_sub_study.analysis_environments = [
            models.ChemicalEnvironment.unique(
                db, models.ChemicalEnvironment(id=x.value)
            )
            for x in sub_study.analysis_environments
        ]

        return db_sub_study

    @classmethod
    def delete(cls, db: Session, project_id: str, study_id: str, sub_study_id: str):

        db_sub_study = cls.query(db, project_id, study_id, sub_study_id)

        if not db_sub_study:
            raise cls.not_found_error()(project_id, study_id, sub_study_id)

        cls._check_has_dependants(db, db_sub_study, UnableToDeleteError)

        original_force_field = db_sub_study.force_field
        db_sub_study.force_field = None

        db.delete(db_sub_study)

        if original_force_field is not None:
            ForceFieldCRUD.delete(db, original_force_field)

    @classmethod
    @abc.abstractmethod
    def _model_kwargs(
        cls,
        db_sub_study: models.SubStudy,
    ) -> Dict[str, Any]:
        """Returns the kwargs to create a new model with."""

        db_parent_study = db_sub_study.parent
        db_parent_project = db_parent_study.parent

        return dict(
            id=db_sub_study.identifier,
            study_id=db_parent_study.identifier,
            project_id=db_parent_project.identifier,
            name=db_sub_study.name,
            description=db_sub_study.description,
            force_field=db_sub_study.force_field,
            optimization_id=(
                None
                if db_sub_study.optimization is None
                else db_sub_study.optimization.identifier
            ),
            analysis_environments=[
                ChemicalEnvironment(x.id) for x in db_sub_study.analysis_environments
            ],
        )

    @classmethod
    def db_to_model(cls, db_sub_study: models.SubStudy) -> projects.SubStudy:

        sub_study = cls.rest_class()(**cls._model_kwargs(db_sub_study))
        return sub_study


class OptimizationCRUD(SubStudyCRUD):
    @classmethod
    def orm_class(cls):
        return models.Optimization

    @classmethod
    def rest_class(cls):
        return projects.Optimization

    @classmethod
    def attribute_name(cls) -> str:
        return "optimizations"

    @classmethod
    def exists_error(cls):
        return OptimizationExistsError

    @classmethod
    def not_found_error(cls):
        return OptimizationNotFoundError

    @classmethod
    def _db_model_kwargs(
        cls,
        db: Session,
        sub_study: projects.Optimization,
        db_parent: models.Study,
        db_force_field: Optional[models.ForceField],
    ) -> Dict[str, Any]:
        """Returns the kwargs to create a new database model with."""

        db_model_kwargs = super(OptimizationCRUD, cls)._db_model_kwargs(
            db, sub_study, db_parent, db_force_field
        )
        # noinspection PyTypeChecker
        db_model_kwargs.update(
            dict(
                evaluator_targets=[
                    EvaluatorTargetCRUD.model_to_db(db, target)
                    for target in sub_study.targets
                    if isinstance(target, EvaluatorTarget)
                ],
                recharge_targets=[
                    RechargeTargetCRUD.model_to_db(db, target)
                    for target in sub_study.targets
                    if isinstance(target, RechargeTarget)
                ],
                parameters_to_train=[
                    ParameterCRUD.create(db, x) for x in sub_study.parameters_to_train
                ],
                force_balance_engine=(
                    None
                    if not isinstance(sub_study.engine, ForceBalance)
                    else models.ForceBalance(
                        **sub_study.engine.dict(exclude={"priors", "type"}),
                        priors=[
                            models.ForceBalancePrior(parameter_type=key, value=value)
                            for key, value in sub_study.engine.priors.items()
                        ],
                    )
                ),
                max_iterations=sub_study.max_iterations,
            )
        )

        return db_model_kwargs

    @classmethod
    def check_has_children(
        cls,
        db_sub_study: models.Optimization,
        error_type: Type[Union[UnableToUpdateError, UnableToDeleteError]],
    ):

        study_id = db_sub_study.parent.identifier
        project_id = db_sub_study.parent.parent.identifier

        if db_sub_study.children is not None and len(db_sub_study.children) > 0:

            child_optimization_ids = [
                x.identifier for x in db_sub_study.children if x.type == "optimization"
            ]
            child_benchmark_ids = [
                x.identifier for x in db_sub_study.children if x.type == "benchmark"
            ]
            optimizations_string = (
                ""
                if len(child_optimization_ids) == 0
                else f"optimizations (with ids={', '.join(child_optimization_ids)})"
            )
            benchmarks_string = (
                ""
                if len(child_benchmark_ids) == 0
                else f"benchmarks (with ids={', '.join(child_benchmark_ids)})"
            )
            join_string = "" if len(child_optimization_ids) == 0 else " and "

            raise error_type(
                f"This optimization (project_id={project_id}, study_id={study_id}, "
                f"optimization_id={db_sub_study.identifier}) has {optimizations_string}"
                f"{join_string}{benchmarks_string} associated with it and so cannot be "
                f"updated. Delete the dependants first and then try again."
            )

    @classmethod
    def _check_has_dependants(
        cls,
        db: Session,
        db_sub_study: models.Optimization,
        error_type: Type[Union[UnableToUpdateError, UnableToDeleteError]],
    ):

        # Make sure the optimization has no children, e.g. other sub-studies
        # such as optimizations and benchmarks which depend on the refit force
        # field produced by this optimization.
        cls.check_has_children(db_sub_study, error_type)

        # Make sure the optimization does not have any results uploaded yet.
        study_id = db_sub_study.parent.identifier
        project_id = db_sub_study.parent.parent.identifier

        if db_sub_study.results is not None:

            error_verb = (
                "updated" if isinstance(error_type, UnableToUpdateError) else "deleted"
            )

            raise error_type(
                f"This optimization (project_id={project_id}, "
                f"study_id={study_id}, optimization_id={db_sub_study.identifier}) "
                f"already has a set of results associated with it so cannot be "
                f"{error_verb}. Delete the results first and then try again."
            )

    @classmethod
    def update(cls, db: Session, sub_study: projects.Optimization):

        db_optimization = super(OptimizationCRUD, cls).update(db, sub_study)

        # Update the optimization engine.
        # noinspection PyTypeChecker
        db_optimization.force_balance_engine = (
            None
            if not isinstance(sub_study.engine, ForceBalance)
            else models.ForceBalance(
                **sub_study.engine.dict(exclude={"priors", "type"}),
                priors=[
                    models.ForceBalancePrior(parameter_type=key, value=value)
                    for key, value in sub_study.engine.priors.items()
                ],
            )
        )

        # Update the targets.
        db_optimization.evaluator_targets = [
            EvaluatorTargetCRUD.model_to_db(db, target)
            for target in sub_study.targets
            if isinstance(target, EvaluatorTarget)
        ]
        db_optimization.recharge_targets = [
            RechargeTargetCRUD.model_to_db(db, target)
            for target in sub_study.targets
            if isinstance(target, RechargeTarget)
        ]

        # Update the maximum number of iterations
        db_optimization.max_iterations = sub_study.max_iterations

        # Update the parameters to be optimized.
        db_optimization.parameters_to_train = [
            ParameterCRUD.create(db, x) for x in sub_study.parameters_to_train
        ]

        return db_optimization

    @staticmethod
    def _db_engine_to_model(db_engine: models.ForceBalance) -> ForceBalance:

        # noinspection PyTypeChecker
        return ForceBalance(
            convergence_step_criteria=db_engine.convergence_step_criteria,
            convergence_objective_criteria=db_engine.convergence_objective_criteria,
            convergence_gradient_criteria=db_engine.convergence_gradient_criteria,
            n_criteria=db_engine.n_criteria,
            initial_trust_radius=db_engine.initial_trust_radius,
            minimum_trust_radius=db_engine.minimum_trust_radius,
            priors={x.parameter_type: x.value for x in db_engine.priors},
        )

    @classmethod
    def _model_kwargs(
        cls,
        db_sub_study: models.Optimization,
    ) -> Dict[str, Any]:
        """Returns the kwargs to create a new model with."""

        model_kwargs = super(OptimizationCRUD, cls)._model_kwargs(db_sub_study)
        model_kwargs.update(
            dict(
                parameters_to_train=db_sub_study.parameters_to_train,
                engine=OptimizationCRUD._db_engine_to_model(
                    db_sub_study.force_balance_engine
                ),
                targets=[
                    *[
                        EvaluatorTargetCRUD.db_to_model(evaluator_target)
                        for evaluator_target in db_sub_study.evaluator_targets
                    ],
                    *[
                        RechargeTargetCRUD.db_to_model(recharge_target)
                        for recharge_target in db_sub_study.recharge_targets
                    ],
                ],
                max_iterations=db_sub_study.max_iterations,
            )
        )

        return model_kwargs


class BenchmarkCRUD(SubStudyCRUD):
    @classmethod
    def orm_class(cls):
        return models.Benchmark

    @classmethod
    def rest_class(cls):
        return projects.Benchmark

    @classmethod
    def attribute_name(cls) -> str:
        return "benchmarks"

    @classmethod
    def exists_error(cls):
        return BenchmarkExistsError

    @classmethod
    def not_found_error(cls):
        return BenchmarkNotFoundError

    @classmethod
    def _check_dependencies_exist(cls, db: Session, sub_study: projects.Benchmark):

        super(BenchmarkCRUD, cls)._check_dependencies_exist(db, sub_study)

        # Check that all of the test sets exist.
        test_sets = [DataSetCRUD.query(db, x) for x in sub_study.test_set_ids]

        if any(x is None for x in test_sets):

            raise DataSetNotFoundError(
                next(
                    iter(
                        x
                        for x, y in zip(sub_study.test_set_ids, test_sets)
                        if y is None
                    )
                )
            )

        # Check that any referenced optimization results exist.
        if sub_study.optimization_id is None:
            return

        db_optimization = OptimizationCRUD.query(
            db, sub_study.project_id, sub_study.study_id, sub_study.optimization_id
        )

        if db_optimization.results is None:
            raise UnableToCreateError(
                f"The benchmark is for an optimization ("
                f"id={sub_study.optimization_id}) which does not have any results "
                f"uploaded yet. Upload results for the optimization and then try "
                f"again."
            )

    @classmethod
    def _db_model_kwargs(
        cls,
        db: Session,
        sub_study: projects.Benchmark,
        db_parent: models.Study,
        db_force_field: Optional[models.ForceField],
    ) -> Dict[str, Any]:
        """Returns the kwargs to create a new database model with."""

        db_model_kwargs = super(BenchmarkCRUD, cls)._db_model_kwargs(
            db, sub_study, db_parent, db_force_field
        )
        # noinspection PyTypeChecker
        db_model_kwargs.update(
            dict(test_sets=[DataSetCRUD.query(db, x) for x in sub_study.test_set_ids])
        )

        return db_model_kwargs

    @classmethod
    def _check_has_dependants(
        cls,
        db: Session,
        db_sub_study: models.Benchmark,
        error_type: Type[Union[UnableToUpdateError, UnableToDeleteError]],
    ):

        study_id = db_sub_study.parent.identifier
        project_id = db_sub_study.parent.parent.identifier

        if db_sub_study.results is not None:

            raise error_type(
                f"This benchmark (project_id={project_id}, "
                f"study_id={study_id}, benchmark_id={db_sub_study.identifier}) "
                f"already has a set of results associated with it so cannot be "
                f"updated. Delete the results first and then update."
            )

    @classmethod
    def update(cls, db: Session, sub_study: projects.Benchmark):

        try:
            db_benchmark = super(BenchmarkCRUD, cls).update(db, sub_study)
        except UnableToCreateError as e:
            raise UnableToUpdateError(e.detail)
        except Exception as e:
            raise e

        # Update the test sets.
        db_benchmark.test_sets = [
            DataSetCRUD.query(db, x) for x in sub_study.test_set_ids
        ]

        # Update the optimization possibly being benchmarked.
        db_benchmark.optimization = (
            None
            if sub_study.optimization_id is None
            else OptimizationCRUD.query(
                db, sub_study.project_id, sub_study.study_id, sub_study.optimization_id
            )
        )

        return db_benchmark

    @classmethod
    def _model_kwargs(
        cls,
        db_sub_study: models.Benchmark,
    ) -> Dict[str, Any]:
        """Returns the kwargs to create a new model with."""

        model_kwargs = super(BenchmarkCRUD, cls)._model_kwargs(db_sub_study)
        model_kwargs.update(dict(test_set_ids=[x.id for x in db_sub_study.test_sets]))

        return model_kwargs


class StudyCRUD:
    @staticmethod
    def query(db: Session, project_id: str, study_id: str):

        db_study = (
            db.query(models.Study)
            .filter(models.Study.identifier == study_id)
            .join(models.Project)
            .filter(models.Project.identifier == project_id)
            .first()
        )

        return db_study

    @staticmethod
    def create(db: Session, study: projects.Study, parent=None) -> models.Study:

        if StudyCRUD.query(db, study.project_id, study.id) is not None:
            raise StudyExistsError(study.project_id, study.id)

        if parent is None:
            parent = ProjectCRUD.query(db, study.project_id)

        if parent is None:
            raise ProjectNotFoundError(study.project_id)

        # noinspection PyTypeChecker
        db_study = models.Study(
            identifier=study.id,
            parent=parent,
            name=study.name,
            description=study.description,
        )

        db_study.optimizations = [
            OptimizationCRUD.create(db, x, db_study) for x in study.optimizations
        ]
        db_study.benchmarks = [
            BenchmarkCRUD.create(db, x, db_study) for x in study.benchmarks
        ]

        return db_study

    @staticmethod
    def read_all(db: Session, project_id):

        db_project = ProjectCRUD.query(db, project_id)

        if not db_project:
            raise ProjectNotFoundError(project_id)

        return [StudyCRUD.db_to_model(x) for x in db_project.studies]

    @staticmethod
    def read(db: Session, project_id: str, study_id: str):

        db_study = StudyCRUD.query(db, project_id, study_id)

        if not db_study:
            raise StudyNotFoundError(project_id, study_id)

        return StudyCRUD.db_to_model(db_study)

    @staticmethod
    def _delete_orphaned(
        db: Session, study: projects.Study, crud_class, db_existing_list, new_list
    ):
        """Attempts to delete any orphaned children (namely optimizations and
        benchmarks) when a study is being updated.

        Parameters
        ----------
        db
            The current data base session.
        crud_class
            The associated CRUD class of the class of orphaned items.
        study
            The study being updated.
        db_existing_list
            A list of the possibly orphaned items which currently exist on the
            data base.
        new_list
            The new list of items being updated / created on the data base.
        """
        ids_to_remove = {x.identifier for x in db_existing_list} - {
            x.id for x in new_list
        }

        for id_to_remove in ids_to_remove:
            crud_class.delete(db, study.project_id, study.id, id_to_remove)

    @staticmethod
    def update(db: Session, study: projects.Study) -> models.Study:

        db_study = StudyCRUD.query(db, study.project_id, study.id)

        if db_study is None:
            raise StudyNotFoundError(study.project_id, study.id)

        db_study.name = study.name
        db_study.description = study.description

        db_optimizations = []
        db_benchmarks = []

        # Remove any orphaned optimizations and benchmarks.
        StudyCRUD._delete_orphaned(
            db, study, OptimizationCRUD, db_study.optimizations, study.optimizations
        )
        StudyCRUD._delete_orphaned(
            db, study, BenchmarkCRUD, db_study.benchmarks, study.benchmarks
        )

        for optimization in study.optimizations:

            db_optimization = OptimizationCRUD.query(
                db, study.project_id, study.id, optimization.id
            )

            if not db_optimization:
                db_optimization = OptimizationCRUD.create(db, optimization)
            else:
                db_optimization = OptimizationCRUD.update(db, optimization)

            db_optimizations.append(db_optimization)

        for benchmark in study.benchmarks:

            db_benchmark = BenchmarkCRUD.query(
                db, study.project_id, study.id, benchmark.id
            )

            if not db_benchmark:
                db_benchmark = BenchmarkCRUD.create(db, benchmark)
            else:
                db_benchmark = BenchmarkCRUD.update(db, benchmark)

            db_benchmarks.append(db_benchmark)

        db_study.optimizations = db_optimizations
        db_study.benchmarks = db_benchmarks

        return db_study

    @staticmethod
    def delete(db: Session, project_id: str, study_id: str):

        db_study = StudyCRUD.query(db, project_id, study_id)

        if not db_study:
            raise StudyNotFoundError(project_id, study_id)

        for optimization in db_study.optimizations:
            OptimizationCRUD.delete(db, project_id, study_id, optimization.identifier)

        for benchmark in db_study.benchmarks:
            BenchmarkCRUD.delete(db, project_id, study_id, benchmark.identifier)

        db.delete(db_study)

    @staticmethod
    def db_to_model(db_study: models.Study) -> projects.Study:

        db_parent_project = db_study.parent

        # noinspection PyTypeChecker
        study = projects.Study(
            id=db_study.identifier,
            project_id=db_parent_project.identifier,
            name=db_study.name,
            description=db_study.description,
            optimizations=[
                OptimizationCRUD.db_to_model(x) for x in db_study.optimizations
            ],
            benchmarks=[BenchmarkCRUD.db_to_model(x) for x in db_study.benchmarks],
        )

        return study


class ProjectCRUD:
    @staticmethod
    def n_total(db: Session):
        """Returns the total number of projects in the database."""
        return db.query(models.Project.id).count()

    @staticmethod
    def query(db: Session, project_id: str):

        db_project = (
            db.query(models.Project)
            .filter(models.Project.identifier == project_id)
            .first()
        )

        return db_project

    @staticmethod
    def create(db: Session, project: projects.Project) -> models.Project:

        if ProjectCRUD.query(db, project.id) is not None:
            raise ProjectExistsError(project.id)

        # noinspection PyTypeChecker
        db_project = models.Project(
            identifier=project.id,
            name=project.name,
            description=project.description,
            authors=[AuthorCRUD.create(db, x) for x in project.authors],
        )

        db_project.studies = [
            StudyCRUD.create(db, x, db_project) for x in project.studies
        ]

        return db_project

    @staticmethod
    def read_all(
        db: Session, skip: int = 0, limit: int = 100, include_children: bool = True
    ):

        db_projects = db.query(models.Project).offset(skip).limit(limit).all()
        return [ProjectCRUD.db_to_model(x, include_children) for x in db_projects]

    @staticmethod
    def read(db: Session, project_id: str):

        db_project = ProjectCRUD.query(db, project_id)

        if db_project is None:
            raise ProjectNotFoundError(project_id)

        return ProjectCRUD.db_to_model(db_project)

    @staticmethod
    def update(db: Session, project: projects.Project) -> models.Project:

        db_project = ProjectCRUD.query(db, project.id)

        if db_project is None:
            raise ProjectNotFoundError(project.id)

        db_project.name = project.name
        db_project.description = project.description

        db_studies = []

        # Remove any orphaned studies.
        study_ids_to_remove = {x.identifier for x in db_project.studies} - {
            x.id for x in project.studies
        }

        for study_id in study_ids_to_remove:
            StudyCRUD.delete(db, project.id, study_id)

        # Update any existing / create any new studies.
        for study in project.studies:

            db_study = StudyCRUD.query(db, project.id, study.id)

            if not db_study:
                db_study = StudyCRUD.create(db, study)
            else:
                db_study = StudyCRUD.update(db, study)

            db_studies.append(db_study)

        db_project.studies = db_studies
        db_project.authors = [AuthorCRUD.create(db, x) for x in project.authors]

        return db_project

    @staticmethod
    def delete(db: Session, project_id: str):

        db_project = ProjectCRUD.query(db, project_id)

        if not db_project:
            raise ProjectNotFoundError(project_id)

        for study in db_project.studies:
            StudyCRUD.delete(db, project_id, study.identifier)

        db.delete(db_project)

    @staticmethod
    def db_to_model(
        db_project: models.Project, include_children: bool = True
    ) -> projects.Project:
        """Maps a database project model to its pydantic counterpart.

        Parameters
        ----------
        db_project
            The database project model.
        include_children
            Whether to attach the child studies to the returned model. If false,
            the studies list will be empty on the returned model.

        Returns
        -------
            The pydantic version of the model.
        """

        # noinspection PyTypeChecker
        project = projects.Project(
            id=db_project.identifier,
            name=db_project.name,
            description=db_project.description,
            authors=db_project.authors,
            studies=[]
            if not include_children
            else [StudyCRUD.db_to_model(x) for x in db_project.studies],
        )

        return project
