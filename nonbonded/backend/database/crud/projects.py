from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.authors import AuthorCRUD
from nonbonded.backend.database.crud.datasets import DataSetCRUD
from nonbonded.backend.database.crud.forcefield import ParameterCRUD
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
from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.utilities.environments import ChemicalEnvironment


class OptimizationCRUD:
    @staticmethod
    def query(
        db: Session, project_id: str, study_id: str, optimization_id: str
    ) -> models.Optimization:

        db_optimization = (
            db.query(models.Optimization)
            .filter(models.Optimization.identifier == optimization_id)
            .join(models.Study)
            .filter(models.Study.identifier == study_id)
            .join(models.Project)
            .filter(models.Project.identifier == project_id)
            .first()
        )

        return db_optimization

    @staticmethod
    def create(
        db: Session, optimization: projects.Optimization, parent=None
    ) -> models.Optimization:

        if (
            OptimizationCRUD.query(
                db, optimization.project_id, optimization.study_id, optimization.id
            )
            is not None
        ):

            raise OptimizationExistsError(
                optimization.project_id, optimization.study_id, optimization.id
            )

        training_sets = [
            DataSetCRUD.query(db, x) for x in optimization.training_set_ids
        ]

        if any(x is None for x in training_sets):

            raise DataSetNotFoundError(
                next(
                    iter(
                        x
                        for x, y in zip(optimization.training_set_ids, training_sets)
                        if y is None
                    )
                )
            )

        if parent is None:
            parent = StudyCRUD.query(db, optimization.project_id, optimization.study_id)

        if parent is None:
            raise StudyNotFoundError(optimization.project_id, optimization.study_id)

        # noinspection PyTypeChecker
        db_optimization = models.Optimization(
            identifier=optimization.id,
            parent=parent,
            name=optimization.name,
            description=optimization.description,
            training_sets=training_sets,
            parameters_to_train=[
                ParameterCRUD.create(db, x) for x in optimization.parameters_to_train
            ],
            force_balance_input=models.ForceBalanceOptions(
                **optimization.force_balance_input.dict()
            ),
            initial_force_field=models.InitialForceField.as_unique(
                db, inner_xml=optimization.initial_force_field.inner_xml
            ),
            denominators=[
                models.Denominator(property_type=key, value=value)
                for key, value in optimization.denominators.items()
            ],
            priors=[
                models.Prior(parameter_type=key, value=value)
                for key, value in optimization.priors.items()
            ],
            analysis_environments=[
                models.ChemicalEnvironment.as_unique(db, id=x.value)
                for x in optimization.analysis_environments
            ],
        )

        return db_optimization

    @staticmethod
    def read_all(db: Session, project_id: str, study_id: str):

        db_study = StudyCRUD.query(db, project_id=project_id, study_id=study_id)

        if not db_study:
            raise StudyNotFoundError(project_id, study_id)

        return [OptimizationCRUD.db_to_model(x) for x in db_study.optimizations]

    @staticmethod
    def read(db: Session, project_id: str, study_id: str, optimization_id: str):

        db_optimization = OptimizationCRUD.query(
            db, project_id, study_id, optimization_id
        )

        if not db_optimization:
            raise OptimizationNotFoundError(project_id, study_id, optimization_id)

        return OptimizationCRUD.db_to_model(db_optimization)

    @staticmethod
    def update(db: Session, optimization: projects.Optimization):

        db_optimization = OptimizationCRUD.query(
            db, optimization.project_id, optimization.study_id, optimization.id
        )

        if not db_optimization:

            raise OptimizationNotFoundError(
                optimization.project_id, optimization.study_id, optimization.id
            )

        if db_optimization.results is not None:

            raise UnableToUpdateError(
                f"This optimization (project_id={optimization.project_id}, "
                f"study_id={optimization.study_id}, optimization_id={optimization.id}) "
                f"already has a set of results associated with it so cannot be "
                f"updated. Delete the results first and then try again."
            )

        if (
            db_optimization.benchmarks is not None
            and len(db_optimization.benchmarks) > 0
        ):

            benchmark_ids = [
                ", ".join(x.identifier for x in db_optimization.benchmarks)
            ]

            raise UnableToUpdateError(
                f"This optimization (project_id={optimization.project_id}, "
                f"study_id={optimization.study_id}, optimization_id={optimization.id}) "
                f"has benchmarks (with ids={benchmark_ids}) associated with it and so "
                f"cannot be updated. Delete the benchmarks first and then try again."
            )

        db_optimization.name = optimization.name
        db_optimization.description = optimization.description

        training_sets = [
            DataSetCRUD.query(db, x) for x in optimization.training_set_ids
        ]

        if any(x is None for x in training_sets):
            raise DataSetNotFoundError(
                next(
                    iter(
                        x
                        for x, y in zip(optimization.training_set_ids, training_sets)
                        if y is None
                    )
                )
            )

        db_optimization.training_sets = training_sets
        db_optimization.initial_force_field = models.InitialForceField.as_unique(
            db, inner_xml=optimization.initial_force_field.inner_xml
        )

        db_optimization.parameters_to_train = [
            ParameterCRUD.create(db, x) for x in optimization.parameters_to_train
        ]

        db_optimization.force_balance_input = models.ForceBalanceOptions(
            **optimization.force_balance_input.dict()
        )
        db_optimization.denominators = [
            models.Denominator(property_type=key, value=value)
            for key, value in optimization.denominators.items()
        ]
        db_optimization.priors = [
            models.Prior(parameter_type=key, value=value)
            for key, value in optimization.priors.items()
        ]

        db_optimization.analysis_environments = [
            models.ChemicalEnvironment.as_unique(db, id=x.value)
            for x in optimization.analysis_environments
        ]

        return OptimizationCRUD.db_to_model(db_optimization)

    @staticmethod
    def delete(db: Session, project_id: str, study_id: str, optimization_id: str):

        db_optimization = OptimizationCRUD.query(
            db, project_id, study_id, optimization_id
        )

        if not db_optimization:
            raise OptimizationNotFoundError(project_id, study_id, optimization_id)

        if db_optimization.results is not None:

            raise UnableToDeleteError(
                f"This optimization (project_id={project_id}, "
                f"study_id={study_id}, optimization_id={optimization_id}) "
                f"already has a set of results associated with it so cannot be "
                f"deleted. Delete the results first and then try again."
            )

        if (
            db_optimization.benchmarks is not None
            and len(db_optimization.benchmarks) > 0
        ):

            benchmark_ids = [
                ", ".join(x.identifier for x in db_optimization.benchmarks)
            ]

            raise UnableToDeleteError(
                f"This optimization (project_id={project_id}, "
                f"study_id={study_id}, optimization_id={optimization_id}) "
                f"has benchmarks (with ids={benchmark_ids}) associated with it and so "
                f"cannot be deleted. Delete the benchmarks first and then try again."
            )

        db.delete(db_optimization)

    @staticmethod
    def db_to_model(db_optimization: models.Optimization) -> projects.Optimization:

        db_parent_study = db_optimization.parent
        db_parent_project = db_parent_study.parent

        # noinspection PyTypeChecker
        optimization = projects.Optimization(
            id=db_optimization.identifier,
            study_id=db_parent_study.identifier,
            project_id=db_parent_project.identifier,
            name=db_optimization.name,
            description=db_optimization.description,
            training_set_ids=[x.id for x in db_optimization.training_sets],
            parameters_to_train=db_optimization.parameters_to_train,
            force_balance_input=db_optimization.force_balance_input,
            initial_force_field=db_optimization.initial_force_field,
            denominators={
                x.property_type: x.value for x in db_optimization.denominators
            },
            priors={x.parameter_type: x.value for x in db_optimization.priors},
            analysis_environments=[
                ChemicalEnvironment(x.id) for x in db_optimization.analysis_environments
            ],
        )

        return optimization


class BenchmarkCRUD:
    @staticmethod
    def query(
        db: Session, project_id: str, study_id: str, benchmark_id: str
    ) -> models.Benchmark:

        db_benchmark = (
            db.query(models.Benchmark)
            .filter(models.Benchmark.identifier == benchmark_id)
            .join(models.Study)
            .filter(models.Study.identifier == study_id)
            .join(models.Project)
            .filter(models.Project.identifier == project_id)
            .first()
        )

        return db_benchmark

    @staticmethod
    def create(
        db: Session, benchmark: projects.Benchmark, parent=None
    ) -> models.Benchmark:

        if (
            BenchmarkCRUD.query(
                db, benchmark.project_id, benchmark.study_id, benchmark.id
            )
            is not None
        ):

            raise BenchmarkExistsError(
                benchmark.project_id, benchmark.study_id, benchmark.id
            )

        test_sets = [DataSetCRUD.query(db, x) for x in benchmark.test_set_ids]

        if any(x is None for x in test_sets):

            raise DataSetNotFoundError(
                next(
                    iter(
                        x
                        for x, y in zip(benchmark.test_set_ids, test_sets)
                        if y is None
                    )
                )
            )

        db_optimization = None

        if benchmark.optimization_id is not None:

            db_optimization = OptimizationCRUD.query(
                db, benchmark.project_id, benchmark.study_id, benchmark.optimization_id
            )

            if db_optimization is None:

                raise OptimizationNotFoundError(
                    benchmark.project_id, benchmark.study_id, benchmark.optimization_id
                )

            if db_optimization.results is None:

                raise UnableToCreateError(
                    f"The benchmark is for an optimization ("
                    f"id={benchmark.optimization_id}) which does not have any results "
                    f"uploaded yet. Upload results for the optimization and then try "
                    f"again."
                )

        if parent is None:
            parent = StudyCRUD.query(db, benchmark.project_id, benchmark.study_id)

        if parent is None:
            raise StudyNotFoundError(benchmark.project_id, benchmark.study_id)

        db_benchmark = models.Benchmark(
            identifier=benchmark.id,
            parent=parent,
            name=benchmark.name,
            description=benchmark.description,
            test_sets=test_sets,
            optimization=db_optimization,
            force_field_name=benchmark.force_field_name,
            analysis_environments=[
                models.ChemicalEnvironment.as_unique(db, id=x.value)
                for x in benchmark.analysis_environments
            ],
        )

        return db_benchmark

    @staticmethod
    def read_all(db: Session, project_id: str, study_id: str):

        db_study = StudyCRUD.query(db, project_id=project_id, study_id=study_id)

        if not db_study:
            raise StudyNotFoundError(project_id, study_id)

        return [BenchmarkCRUD.db_to_model(x) for x in db_study.benchmarks]

    @staticmethod
    def read(db: Session, project_id: str, study_id: str, benchmark_id: str):

        db_benchmark = BenchmarkCRUD.query(db, project_id, study_id, benchmark_id)

        if not db_benchmark:
            raise BenchmarkNotFoundError(project_id, study_id, benchmark_id)

        return BenchmarkCRUD.db_to_model(db_benchmark)

    @staticmethod
    def update(db: Session, benchmark: projects.Benchmark):

        db_benchmark = BenchmarkCRUD.query(
            db, benchmark.project_id, benchmark.study_id, benchmark.id
        )

        if not db_benchmark:

            raise BenchmarkNotFoundError(
                benchmark.project_id, benchmark.study_id, benchmark.id
            )

        if db_benchmark.results is not None:

            raise UnableToUpdateError(
                f"This benchmark (project_id={benchmark.project_id}, "
                f"study_id={benchmark.study_id}, benchmark_id={benchmark.id}) "
                f"already has a set of results associated with it so cannot be "
                f"updated. Delete the results first and then update."
            )

        db_benchmark.name = benchmark.name
        db_benchmark.description = benchmark.description

        test_sets = [DataSetCRUD.query(db, x) for x in benchmark.test_set_ids]

        if any(x is None for x in test_sets):

            raise DataSetNotFoundError(
                next(
                    iter(
                        x
                        for x, y in zip(benchmark.test_set_ids, test_sets)
                        if y is None
                    )
                )
            )

        db_benchmark.test_sets = test_sets

        db_benchmark.force_field_name = benchmark.force_field_name

        if benchmark.optimization_id is not None:

            db_optimization = OptimizationCRUD.query(
                db, benchmark.project_id, benchmark.study_id, benchmark.optimization_id
            )

            if db_optimization is None:

                raise OptimizationNotFoundError(
                    benchmark.project_id, benchmark.study_id, benchmark.optimization_id
                )

            db_benchmark.optimization = db_optimization

        db_benchmark.analysis_environments = [
            models.ChemicalEnvironment.as_unique(db, id=x.value)
            for x in benchmark.analysis_environments
        ]

        return db_benchmark

    @staticmethod
    def delete(db: Session, project_id: str, study_id: str, benchmark_id: str):

        db_benchmark = BenchmarkCRUD.query(db, project_id, study_id, benchmark_id)

        if not db_benchmark:
            raise BenchmarkNotFoundError(project_id, study_id, benchmark_id)

        if db_benchmark.results is not None:

            raise UnableToDeleteError(
                f"This benchmark (project_id={project_id}, "
                f"study_id={study_id}, benchmark_id={benchmark_id}) "
                f"already has a set of results associated with it so cannot be "
                f"deleted. Delete the results first and then try again."
            )

        db.delete(db_benchmark)

    @staticmethod
    def db_to_model(db_benchmark: models.Benchmark) -> projects.Benchmark:

        db_parent_study = db_benchmark.parent
        db_parent_project = db_parent_study.parent

        optimization_id = None

        if db_benchmark.optimization is not None:
            optimization_id = db_benchmark.optimization.identifier

        benchmark = projects.Benchmark(
            id=db_benchmark.identifier,
            study_id=db_parent_study.identifier,
            project_id=db_parent_project.identifier,
            name=db_benchmark.name,
            description=db_benchmark.description,
            test_set_ids=[x.id for x in db_benchmark.test_sets],
            optimization_id=optimization_id,
            force_field_name=db_benchmark.force_field_name,
            analysis_environments=[
                ChemicalEnvironment(x.id) for x in db_benchmark.analysis_environments
            ],
        )

        return benchmark


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
    def read_all_data_sets(
        db: Session, project_id: str, study_id: str
    ) -> DataSetCollection:

        db_study = StudyCRUD.query(db, project_id, study_id)

        if not db_study:
            raise StudyNotFoundError(project_id, study_id)

        data_set_ids = set()

        for optimization in db_study.optimizations:
            data_set_ids.update(x.id for x in optimization.training_sets)
        for benchmark in db_study.benchmarks:
            data_set_ids.update(x.id for x in benchmark.test_sets)

        data_sets = []

        for data_set_id in data_set_ids:

            db_data_set = DataSetCRUD.query(db, data_set_id)
            data_sets.append(DataSetCRUD.db_to_model(db_data_set))

        return DataSetCollection(data_sets=data_sets)

    @staticmethod
    def update(db: Session, study: projects.Study) -> models.Study:

        db_study = StudyCRUD.query(db, study.project_id, study.id)

        if db_study is None:
            raise StudyNotFoundError(study.project_id, study.id)

        db_study.name = study.name
        db_study.description = study.description

        db_optimizations = []
        db_benchmarks = []

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
    def read_all(db: Session, skip: int = 0, limit: int = 100):

        db_projects = db.query(models.Project).offset(skip).limit(limit).all()
        return [ProjectCRUD.db_to_model(x) for x in db_projects]

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
    def db_to_model(db_project: models.Project) -> projects.Project:

        # noinspection PyTypeChecker
        project = projects.Project(
            id=db_project.identifier,
            name=db_project.name,
            description=db_project.description,
            authors=db_project.authors,
            studies=[StudyCRUD.db_to_model(x) for x in db_project.studies],
        )

        return project
