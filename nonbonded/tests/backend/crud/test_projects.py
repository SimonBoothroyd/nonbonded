import functools

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.datasets import DataSetCRUD
from nonbonded.backend.database.crud.projects import (
    BenchmarkCRUD,
    OptimizationCRUD,
    ProjectCRUD,
    StudyCRUD,
)
from nonbonded.backend.database.crud.results import OptimizationResultCRUD
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
from nonbonded.library.models.authors import Author
from nonbonded.library.models.forcefield import ForceField, Parameter
from nonbonded.library.utilities.environments import ChemicalEnvironment
from nonbonded.tests.backend.crud.utilities import (
    create_and_compare_models,
    paginate_models,
    update_and_compare_model,
)
from nonbonded.tests.backend.crud.utilities.commit import (
    commit_benchmark,
    commit_data_set_collection,
    commit_optimization,
    commit_optimization_result,
    commit_project,
    commit_study,
)
from nonbonded.tests.backend.crud.utilities.comparison import (
    compare_benchmarks,
    compare_optimizations,
    compare_projects,
    compare_studies,
)
from nonbonded.tests.backend.crud.utilities.create import (
    create_author,
    create_benchmark,
    create_empty_project,
    create_empty_study,
    create_optimization,
    create_optimization_result,
)


class TestProjectCRUD:
    def test_create_read_empty(self, db: Session):
        """Test that an empty project (i.e. one without studies) can be created, and then
        read back out again while maintaining the integrity of the data.
        """

        project_id = "project-1"
        project = create_empty_project(project_id)

        create_and_compare_models(
            db,
            project,
            ProjectCRUD.create,
            ProjectCRUD.read_all,
            functools.partial(ProjectCRUD.read, project_id=project_id),
            compare_projects,
        )

        # Make sure projects with duplicate ids cannot be added.
        with pytest.raises(ProjectExistsError):
            ProjectCRUD.create(db, project)

    def test_create_read(self, db: Session):
        """Test that a project containing studies can be created, and then
        read back out again while maintaining the integrity of the data.
        """

        project = create_empty_project("project-1")
        project.studies = [create_empty_study(project.id, "study-1")]

        create_and_compare_models(
            db,
            project,
            ProjectCRUD.create,
            ProjectCRUD.read_all,
            functools.partial(ProjectCRUD.read, project_id=project.id),
            compare_projects,
        )

    def test_update_empty(self, db: Session):
        """Test that an empty project (i.e. one without studies) can be correctly
        updated.
        """
        from nonbonded.backend.database.models.projects import author_projects_table

        project = commit_project(db)

        # Test simple text updates
        updated_project = project.copy()
        updated_project.name += " Updated"
        updated_project.description += " Updated"

        update_and_compare_model(
            db,
            updated_project,
            ProjectCRUD.update,
            functools.partial(ProjectCRUD.read, project_id=project.id),
            compare_projects,
        )

        # Test adding a new author.
        updated_project.authors = [
            *updated_project.authors,
            Author(name="Fake Name 2", email="fake@email2.com", institute="Fake"),
        ]
        update_and_compare_model(
            db,
            updated_project,
            ProjectCRUD.update,
            functools.partial(ProjectCRUD.read, project_id=project.id),
            compare_projects,
        )

        # Make sure the authors list looks as expected
        assert db.query(models.Author.email).count() == 2

        # Test removing an author.
        updated_project.authors = [create_author()]
        update_and_compare_model(
            db,
            updated_project,
            ProjectCRUD.update,
            functools.partial(ProjectCRUD.read, project_id=project.id),
            compare_projects,
        )

        # Make sure the author was removed from the association table
        assert db.query(author_projects_table).count() == 1

        # Test that adding an invalid author raises the correct exception.
        bad_updated_project = updated_project.copy()
        bad_updated_project.authors = [
            Author(**{**create_author().dict(), "name": "Fake 2"})
        ]

        with pytest.raises(IntegrityError):
            update_and_compare_model(
                db,
                bad_updated_project,
                ProjectCRUD.update,
                functools.partial(ProjectCRUD.read, project_id=project.id),
                compare_projects,
            )

    def test_update_studies(self, db: Session):
        """Test that an project studies can be correctly updated.
        """

        # Create the parent project.
        project = commit_project(db)

        # Attempt to add a new study by updating the existing project.
        project.studies = [create_empty_study(project.id, "study-1")]

        update_and_compare_model(
            db,
            project,
            ProjectCRUD.update,
            functools.partial(ProjectCRUD.read, project_id=project.id),
            compare_projects,
        )

        assert db.query(models.Study.id).count() == 1

        # Attempt to update the study through a project update.
        project.studies[0].name = "Updated"

        update_and_compare_model(
            db,
            project,
            ProjectCRUD.update,
            functools.partial(ProjectCRUD.read, project_id=project.id),
            compare_projects,
        )

        assert StudyCRUD.query(db, project.id, "study-1").name == "Updated"

        # Attempt to remove the study via project updates.
        project.studies = []

        update_and_compare_model(
            db,
            project,
            ProjectCRUD.update,
            functools.partial(ProjectCRUD.read, project_id=project.id),
            compare_projects,
        )

        assert db.query(models.Study.id).count() == 0

    def test_delete_empty(self, db: Session):
        """Test that an empty project (i.e. one without studies) can be correctly
        deleted.
        """
        from nonbonded.backend.database.models.projects import author_projects_table

        project = commit_project(db)

        assert db.query(models.Author.id).count() == 1

        ProjectCRUD.delete(db, project.id)
        db.commit()

        assert db.query(models.Project.id).count() == 0
        assert db.query(models.Author.id).count() == 1
        assert db.query(author_projects_table).count() == 0

    def test_delete(self, db: Session):
        """Test that a projects studies also get deleted when it gets deleted.
        """

        project, _ = commit_study(db)

        assert db.query(models.Study.id).count() == 1

        ProjectCRUD.delete(db, project.id)
        db.commit()

        assert db.query(models.Study.id).count() == 0

    def test_pagination(self, db: Session):
        """Test that the limit and skip options to read_all have been
        implemented correctly.
        """

        paginate_models(
            db=db,
            models_to_create=[
                create_empty_project("project-1"),
                create_empty_project("project-2"),
                create_empty_project("project-3"),
            ],
            create_function=ProjectCRUD.create,
            read_all_function=ProjectCRUD.read_all,
            compare_function=compare_projects,
        )

    def test_delete_not_found(self, db: Session):

        with pytest.raises(ProjectNotFoundError):
            ProjectCRUD.delete(db, "project-id")

    def test_duplicate_id(self, db: Session):
        """Make sure the database integrity tests catch
        adding two projects with the same id in the same commit.
        """

        # Test adding duplicates in the same commit.
        project_id = "project-1"
        project = create_empty_project(project_id)

        db_project_1 = ProjectCRUD.create(db, project)
        db_project_2 = ProjectCRUD.create(db, project)

        db.add(db_project_1)
        db.add(db_project_2)

        with pytest.raises(IntegrityError):
            db.commit()


class TestStudyCRUD:
    def test_create_read_empty(self, db: Session):
        """Test that a study can be successfully created and then
        retrieved out again while maintaining the integrity of the data.
        """

        parent = commit_project(db)
        study = create_empty_study(parent.id, "study-1")

        create_and_compare_models(
            db,
            study,
            StudyCRUD.create,
            functools.partial(StudyCRUD.read_all, project_id=parent.id),
            functools.partial(StudyCRUD.read, project_id=parent.id, study_id=study.id),
            compare_studies,
        )

        # Test that adding a new study with the same id raises an exception
        with pytest.raises(StudyExistsError):

            create_and_compare_models(
                db, study, StudyCRUD.create, None, StudyCRUD.read, compare_studies,
            )

    def test_update_empty(self, db: Session):
        """Test that an empty study (i.e. one without optimization and benchmarks)
        can be correctly updated.
        """
        _, study = commit_study(db)

        # Test simple text updates
        updated_study = study.copy()
        updated_study.name += " Updated"
        updated_study.description += " Updated"

        update_and_compare_model(
            db,
            updated_study,
            StudyCRUD.update,
            functools.partial(
                StudyCRUD.read, project_id=study.project_id, study_id=study.id
            ),
            compare_studies,
        )

    def test_missing_parent(self, db: Session):
        """Test that an exception is raised when a study is added but
        the parent project cannot be found.
        """

        study = create_empty_study("project-1", "study-1")

        with pytest.raises(ProjectNotFoundError):

            create_and_compare_models(
                db, study, StudyCRUD.create, None, StudyCRUD.read, compare_studies,
            )

    def test_not_found(self, db: Session):
        """Test that an exception is raised when a optimization could
        not be found be it's unique id.
        """

        with pytest.raises(StudyNotFoundError):
            StudyCRUD.read(db, " ", " ")

    def test_delete_empty(self, db: Session):
        """Test that an empty study (i.e. one without any children) can be correctly
        deleted.
        """

        project, study = commit_study(db)

        db_project = ProjectCRUD.query(db, project.id)
        assert len(db_project.studies) == 1

        StudyCRUD.delete(db, project.id, study.id)
        db.commit()

        assert db.query(models.Study.id).count() == 0

        db_project = ProjectCRUD.query(db, project.id)
        assert len(db_project.studies) == 0

    def test_delete_not_found(self, db: Session):

        # Try to delete a study when there is no project or study
        with pytest.raises(StudyNotFoundError):
            StudyCRUD.delete(db, "project-1", "study-id")

        # Try to delete a study when there is only a project but no study
        project = commit_project(db)

        with pytest.raises(StudyNotFoundError):
            StudyCRUD.delete(db, project.id, "study-id")


class TestOptimizationCRUD:
    # TODO: delete (+ benchmark checks).
    # TODO: update (+ benchmark checks).

    def test_create_read_no_results(self, db: Session):
        """Test that a optimization can be successfully created and then
        retrieved out again while maintaining the integrity of the data.
        """

        training_set_ids = [x.id for x in commit_data_set_collection(db).data_sets]

        project, study = commit_study(db)

        optimization = create_optimization(
            project.id, study.id, "optimization-1", training_set_ids
        )

        create_and_compare_models(
            db,
            optimization,
            OptimizationCRUD.create,
            functools.partial(
                OptimizationCRUD.read_all, project_id=project.id, study_id=study.id
            ),
            functools.partial(
                OptimizationCRUD.read,
                project_id=project.id,
                study_id=study.id,
                optimization_id=optimization.id,
            ),
            compare_optimizations,
        )

        # Test that adding a new optimization with the same id raises an exception
        with pytest.raises(OptimizationExistsError):

            create_and_compare_models(
                db,
                optimization,
                OptimizationCRUD.create,
                None,
                OptimizationCRUD.read,
                compare_optimizations,
            )

    def test_missing_data_sets(self, db: Session):
        """Test to make sure an error is raised when the training sets
        cannot be found when creating a new optimization.
        """
        project, study = commit_study(db)

        optimization = create_optimization(
            project.id, study.id, "optimization-1", ["x"]
        )

        with pytest.raises(DataSetNotFoundError):
            create_and_compare_models(
                db,
                optimization,
                OptimizationCRUD.create,
                None,
                OptimizationCRUD.read,
                compare_optimizations,
            )

    def test_missing_parent(self, db: Session):
        """Test that an exception is raised when a optimization is added but
        the parent project or study cannot be found.
        """

        training_set_ids = [x.id for x in commit_data_set_collection(db).data_sets]

        optimization = create_optimization(
            "project-1", "study-1", "optimization-1", training_set_ids
        )

        with pytest.raises(StudyNotFoundError):

            create_and_compare_models(
                db,
                optimization,
                OptimizationCRUD.create,
                None,
                OptimizationCRUD.read,
                compare_optimizations,
            )

    def test_not_found(self, db: Session):
        """Test that an exception is raised when a optimization could
        not be found be it's unique id.
        """

        with pytest.raises(OptimizationNotFoundError):
            OptimizationCRUD.read(db, " ", " ", " ")

    def test_data_set_delete(self, db: Session):
        """Tests that trying to delete a data set which is referenced by an
        optimization yields to an integrity error.
        """

        _, _, optimization, data_set_collection = commit_optimization(db)

        with pytest.raises(UnableToDeleteError) as error_info:
            DataSetCRUD.delete(db, data_set_collection.data_sets[0].id)
            db.commit()

        assert "optimization" in str(error_info.value)

        # After deleting the optimization, the data sets should be deletable.
        OptimizationCRUD.delete(
            db, optimization.project_id, optimization.study_id, optimization.id
        )
        db.commit()

        for data_set_id in optimization.training_set_ids:
            DataSetCRUD.delete(db, data_set_id)

        db.commit()

    def test_delete_no_results(self, db: Session):
        """Test that an optimization which has not yet had results uploaded can
        be successfully deleted and that it's children are also removed.
        """
        from nonbonded.backend.database.models.projects import (
            optimization_training_table,
        )

        project, study, optimization, _ = commit_optimization(db)

        assert db.query(models.Optimization.id).count() == 1
        assert db.query(models.DataSet.id).count() == 2
        assert db.query(models.InitialForceField.id).count() == 1
        assert db.query(models.Parameter.id).count() == len(
            optimization.parameters_to_train
        )
        assert db.query(models.ForceBalanceOptions.id).count() == 1
        assert db.query(models.Denominator.id).count() == len(optimization.denominators)
        assert db.query(models.Prior.id).count() == len(optimization.priors)
        assert db.query(models.ChemicalEnvironment.id).count() == len(
            optimization.analysis_environments
        )
        assert db.query(optimization_training_table).count() == 2

        OptimizationCRUD.delete(db, project.id, study.id, optimization.id)
        db.commit()

        assert db.query(models.Optimization.id).count() == 0
        assert db.query(models.InitialForceField.id).count() == 0
        assert db.query(models.Parameter.id).count() == 0
        assert db.query(models.ForceBalanceOptions.id).count() == 0
        assert db.query(models.Denominator.id).count() == 0
        assert db.query(models.Prior.id).count() == 0
        assert db.query(optimization_training_table).count() == 0

        # These should not be deleted.
        assert db.query(models.DataSet.id).count() == 2
        assert db.query(models.ChemicalEnvironment.id).count() == len(
            optimization.analysis_environments
        )

    def test_delete_not_found(self, db: Session):

        with pytest.raises(OptimizationNotFoundError):
            OptimizationCRUD.delete(db, "project-1", "study-id", "optimization-id")

    def test_update_no_results(self, db: Session):
        """Test that an optimization without any results uploaded
        can be correctly updated.
        """
        from nonbonded.backend.database.models.projects import (
            optimization_training_table,
        )

        _, _, optimization, _ = commit_optimization(db)

        # Test simple 'on-model' updates
        read_function = functools.partial(
            OptimizationCRUD.read,
            project_id=optimization.project_id,
            study_id=optimization.study_id,
            optimization_id=optimization.id,
        )

        updated_optimization = optimization.copy()
        updated_optimization.name += " Updated"
        updated_optimization.description += " Updated"
        updated_optimization.force_balance_input.max_iterations = 2
        updated_optimization.denominators = {"EnthalpyOfVaporization": " "}
        updated_optimization.priors = {"vdW/Atom/sigma": 0.1}
        updated_optimization.analysis_environments = [ChemicalEnvironment.Hydroxy]

        update_and_compare_model(
            db,
            updated_optimization,
            OptimizationCRUD.update,
            read_function,
            compare_optimizations,
        )

        # Try adding / removing training sets via updates.
        updated_optimization.training_set_ids = [optimization.training_set_ids[0]]

        assert db.query(optimization_training_table).count() == 2

        update_and_compare_model(
            db,
            updated_optimization,
            OptimizationCRUD.update,
            read_function,
            compare_optimizations,
        )

        assert db.query(optimization_training_table).count() == 1

        updated_optimization.training_set_ids = optimization.training_set_ids

        update_and_compare_model(
            db,
            updated_optimization,
            OptimizationCRUD.update,
            read_function,
            compare_optimizations,
        )

        assert db.query(optimization_training_table).count() == 2

        # Try adding / removing a parameter to train via updates.
        assert db.query(models.Parameter.id).count() == 1

        updated_optimization.parameters_to_train = [
            Parameter(handler_type="vdW", smirks="[#6:1]", attribute_name="epsilon"),
            Parameter(handler_type="vdW", smirks="[#6:1]", attribute_name="sigma"),
        ]

        update_and_compare_model(
            db,
            updated_optimization,
            OptimizationCRUD.update,
            read_function,
            compare_optimizations,
        )

        assert db.query(models.Parameter.id).count() == 2

        updated_optimization.parameters_to_train = [
            Parameter(handler_type="vdW", smirks="[#6:1]", attribute_name="epsilon"),
        ]

        update_and_compare_model(
            db,
            updated_optimization,
            OptimizationCRUD.update,
            read_function,
            compare_optimizations,
        )

        assert db.query(models.Parameter.id).count() == 1

        # Make sure the force field to retrain can be altered, and the
        # old one is correctly removed when a new one is used.
        assert db.query(models.InitialForceField.id).count() == 1

        updated_optimization.initial_force_field = ForceField(
            inner_xml="<root>Updated</root"
        )

        update_and_compare_model(
            db,
            updated_optimization,
            OptimizationCRUD.update,
            read_function,
            compare_optimizations,
        )

        assert db.query(models.InitialForceField.id).count() == 1

    def test_update_missing_data_set(self, db: Session):
        """Test that an exception is raised when an optimization is updated to
        target a non-existent data set.
        """

        _, _, optimization, _ = commit_optimization(db)
        optimization.training_set_ids = [" "]

        with pytest.raises(DataSetNotFoundError):

            update_and_compare_model(
                db,
                optimization,
                OptimizationCRUD.update,
                functools.partial(
                    OptimizationCRUD.read,
                    project_id=optimization.project_id,
                    study_id=optimization.study_id,
                    optimization_id=optimization.id,
                ),
                compare_optimizations,
            )

    def test_update_delete_with_results(self, db: Session):
        """Test that an optimization which has results uploaded can only be
        updated / deleted once the results have been deleted.
        """

        project, study, optimization, _, _ = commit_optimization_result(db)

        with pytest.raises(UnableToDeleteError) as error_info:
            OptimizationCRUD.delete(db, project.id, study.id, optimization.id)

        assert "results" in str(error_info.value)

        with pytest.raises(UnableToUpdateError) as error_info:
            OptimizationCRUD.update(db, optimization)

        assert "results" in str(error_info.value)

        # Delete the results and try again.
        OptimizationResultCRUD.delete(db, project.id, study.id, optimization.id)
        db.commit()

        OptimizationCRUD.update(db, optimization)
        OptimizationCRUD.delete(db, project.id, study.id, optimization.id)

    def test_update_delete_with_benchmark(self, db: Session):
        """Test that an optimization which is being targeted by a benchmark can
        only be updated
        updated once the results have been deleted.
        """

        (
            project,
            study,
            benchmark,
            data_set,
            optimization,
            optimization_result,
        ) = commit_benchmark(db, True, None)

        with pytest.raises(UnableToDeleteError) as error_info:
            OptimizationCRUD.delete(db, project.id, study.id, optimization.id)

        assert "benchmark" in str(error_info.value)

        with pytest.raises(UnableToUpdateError) as error_info:
            OptimizationCRUD.update(db, optimization)

        assert "benchmark" in str(error_info.value)

        # Delete the benchmark and results and try again.
        BenchmarkCRUD.delete(db, project.id, study.id, benchmark.id)
        db.commit()
        OptimizationResultCRUD.delete(db, project.id, study.id, optimization.id)
        db.commit()

        OptimizationCRUD.update(db, optimization)
        OptimizationCRUD.delete(db, project.id, study.id, optimization.id)

    def test_update_not_found(self, db: Session):

        optimization = create_optimization(" ", " ", " ", [" "])

        with pytest.raises(OptimizationNotFoundError):
            OptimizationCRUD.update(db, optimization)


class TestBenchmarkCRUD:
    def test_create_read_no_results(self, db: Session):
        """Test that a benchmark can be successfully created and then
        retrieved out again while maintaining the integrity of the data.
        """

        project, study, optimization, test_set = commit_optimization(db)
        test_set_ids = [x.id for x in test_set.data_sets]

        # Add a benchmark which targets an optimization. First check that an exception
        # is rasied when no results have been uploaded yet.
        benchmark = create_benchmark(
            project.id,
            study.id,
            "benchmark-1",
            test_set_ids,
            optimization_id=optimization.id,
            force_field_name=None,
        )

        with pytest.raises(UnableToCreateError):
            create_and_compare_models(
                db,
                benchmark,
                BenchmarkCRUD.create,
                None,
                BenchmarkCRUD.read,
                compare_benchmarks,
            )

        # Upload results and try again.
        db.add(
            OptimizationResultCRUD.create(
                db, create_optimization_result(project.id, study.id, optimization.id)
            )
        )
        db.commit()

        create_and_compare_models(
            db,
            benchmark,
            BenchmarkCRUD.create,
            functools.partial(
                BenchmarkCRUD.read_all, project_id=project.id, study_id=study.id
            ),
            functools.partial(
                BenchmarkCRUD.read,
                project_id=project.id,
                study_id=study.id,
                benchmark_id=benchmark.id,
            ),
            compare_benchmarks,
        )

        # Add a benchmark which targets a specific force field
        benchmark = create_benchmark(
            project.id,
            study.id,
            "benchmark-2",
            test_set_ids,
            optimization_id=None,
            force_field_name="openff-1.0.0.offxml",
        )

        create_and_compare_models(
            db,
            benchmark,
            BenchmarkCRUD.create,
            functools.partial(
                BenchmarkCRUD.read_all, project_id=project.id, study_id=study.id
            ),
            functools.partial(
                BenchmarkCRUD.read,
                project_id=project.id,
                study_id=study.id,
                benchmark_id=benchmark.id,
            ),
            compare_benchmarks,
            n_expected_models=2,
        )

        # Test that adding a new benchmark with the same id raises an exception
        with pytest.raises(BenchmarkExistsError):

            create_and_compare_models(
                db,
                benchmark,
                BenchmarkCRUD.create,
                None,
                BenchmarkCRUD.read,
                compare_benchmarks,
            )

        # Test that adding a benchmark which targets a non-existent optimization
        # causes an exception.
        benchmark = create_benchmark(
            project.id,
            study.id,
            "benchmark-3",
            test_set_ids,
            optimization_id=" ",
            force_field_name=None,
        )

        with pytest.raises(OptimizationNotFoundError):
            create_and_compare_models(
                db,
                benchmark,
                BenchmarkCRUD.create,
                None,
                BenchmarkCRUD.read,
                compare_benchmarks,
            )

    def test_missing_data_sets(self, db: Session):
        """Test to make sure an error is raised when the test sets
        cannot be found when creating a new benchmark.
        """
        project, study = commit_study(db)

        benchmark = create_benchmark(
            project.id, study.id, "benchmark-1", ["x"], None, " "
        )

        with pytest.raises(DataSetNotFoundError):
            create_and_compare_models(
                db,
                benchmark,
                BenchmarkCRUD.create,
                None,
                BenchmarkCRUD.read,
                compare_benchmarks,
            )

    def test_missing_parent(self, db: Session):
        """Test that an exception is raised when a benchmark is added but
        the parent project or study cannot be found.
        """

        test_set_ids = [x.id for x in commit_data_set_collection(db).data_sets]

        benchmark = create_benchmark(
            "project-1", "study-1", "benchmark-1", test_set_ids, None, " "
        )

        with pytest.raises(StudyNotFoundError):

            create_and_compare_models(
                db,
                benchmark,
                BenchmarkCRUD.create,
                None,
                BenchmarkCRUD.read,
                compare_benchmarks,
            )

    def test_not_found(self, db: Session):
        """Test that an exception is raised when a benchmark could
        not be found be it's unique id.
        """

        with pytest.raises(BenchmarkNotFoundError):
            BenchmarkCRUD.read(db, " ", " ", " ")

    def test_data_set_no_results(self, db: Session):
        """Tests that trying to delete a data set which is referenced by a
        benchmark yields to an integrity error.
        """

        _, _, benchmark, data_set_collection, _, _ = commit_benchmark(db, False, " ")

        with pytest.raises(UnableToDeleteError) as error_info:
            DataSetCRUD.delete(db, data_set_collection.data_sets[0].id)
            db.commit()

        assert "benchmark" in str(error_info.value)

        # After deleting the benchmark, the data sets should be deletable.
        BenchmarkCRUD.delete(db, benchmark.project_id, benchmark.study_id, benchmark.id)
        db.commit()

        for data_set_id in benchmark.test_set_ids:
            DataSetCRUD.delete(db, data_set_id)

        db.commit()

    def test_delete_no_results(self, db: Session):
        """Test that a benchmark which has not yet had results uploaded can
        be deleted successfully and that it's children are also removed.
        """
        from nonbonded.backend.database.models.projects import benchmark_test_table

        project, study, benchmark, _, optimization, _ = commit_benchmark(db, True, None)

        assert db.query(models.Benchmark.id).count() == 1
        assert db.query(models.DataSet.id).count() == 2
        assert db.query(models.ChemicalEnvironment.id).count() == len(
            benchmark.analysis_environments
        )
        assert db.query(benchmark_test_table).count() == 2

        assert (
            len(
                OptimizationCRUD.query(
                    db, project.id, study.id, optimization.id
                ).benchmarks
            )
            == 1
        )

        BenchmarkCRUD.delete(db, project.id, study.id, benchmark.id)
        db.commit()

        assert db.query(models.Benchmark.id).count() == 0
        assert db.query(benchmark_test_table).count() == 0
        assert (
            len(
                OptimizationCRUD.query(
                    db, project.id, study.id, optimization.id
                ).benchmarks
            )
            == 0
        )

        # These should not be deleted.
        assert db.query(models.DataSet.id).count() == 2
        assert db.query(models.ChemicalEnvironment.id).count() == len(
            optimization.analysis_environments
        )

    # def test_delete_with_results(self, db: Session):
    #     """Test that a benchmark which has results uploaded can only be
    #     deleted once the results have been deleted.
    #     """
    #
    #     project, study, optimization, _ = commit_benchmark(db, False, " ")
    #
    #     db.add(
    #         OptimizationResultCRUD.create(
    #             db, create_optimization_result(project.id, study.id, optimization.id)
    #         )
    #     )
    #     db.commit()
    #
    #     with pytest.raises(UnableToDeleteError):
    #         OptimizationCRUD.delete(db, project.id, study.id, optimization.id)
    #
    #     # Delete the results and try again.
    #     OptimizationResultCRUD.delete(db, project.id, study.id, optimization.id)
    #     OptimizationCRUD.delete(db, project.id, study.id, optimization.id)

    def test_delete_not_found(self, db: Session):

        with pytest.raises(BenchmarkNotFoundError):
            BenchmarkCRUD.delete(db, "project-1", "study-id", "benchmark-id")

    def test_update_no_results(self, db: Session):
        """Test that a benchmark without any results uploaded can
        be correctly updated.
        """
        from nonbonded.backend.database.models.projects import benchmark_test_table

        _, _, benchmark, _, optimization, _ = commit_benchmark(db, True, None)

        # Test simple text updates
        read_function = functools.partial(
            BenchmarkCRUD.read,
            project_id=benchmark.project_id,
            study_id=benchmark.study_id,
            benchmark_id=benchmark.id,
        )

        updated_benchmark = benchmark.copy()
        updated_benchmark.name += " Updated"
        updated_benchmark.description += " Updated"
        updated_benchmark.analysis_environments = [ChemicalEnvironment.Ketene]

        update_and_compare_model(
            db,
            updated_benchmark,
            BenchmarkCRUD.update,
            read_function,
            compare_benchmarks,
        )

        # Try adding / removing test sets via updates.
        updated_benchmark.test_set_ids = [benchmark.test_set_ids[0]]

        assert db.query(benchmark_test_table).count() == 2

        update_and_compare_model(
            db,
            updated_benchmark,
            BenchmarkCRUD.update,
            read_function,
            compare_benchmarks,
        )

        assert db.query(benchmark_test_table).count() == 1

        updated_benchmark.test_set_ids = benchmark.test_set_ids

        update_and_compare_model(
            db,
            updated_benchmark,
            BenchmarkCRUD.update,
            read_function,
            compare_benchmarks,
        )

        assert db.query(benchmark_test_table).count() == 2

        # Test the the target can be swapped from an optimization
        # to a particular force field and back again.
        assert (
            len(
                OptimizationCRUD.query(
                    db,
                    benchmark.project_id,
                    benchmark.study_id,
                    benchmark.optimization_id,
                ).benchmarks
            )
            == 1
        )

        updated_benchmark.force_field_name = " "
        updated_benchmark.optimization_id = None

        update_and_compare_model(
            db,
            updated_benchmark,
            BenchmarkCRUD.update,
            read_function,
            compare_benchmarks,
        )

        assert (
            len(
                OptimizationCRUD.query(
                    db,
                    benchmark.project_id,
                    benchmark.study_id,
                    benchmark.optimization_id,
                ).benchmarks
            )
            == 0
        )

        updated_benchmark.force_field_name = None
        updated_benchmark.optimization_id = optimization.id

        update_and_compare_model(
            db,
            updated_benchmark,
            BenchmarkCRUD.update,
            read_function,
            compare_benchmarks,
        )

        assert (
            len(
                OptimizationCRUD.query(
                    db,
                    benchmark.project_id,
                    benchmark.study_id,
                    benchmark.optimization_id,
                ).benchmarks
            )
            == 1
        )

    def test_update_missing_data_set(self, db: Session):
        """Test that an exception is raised when a benchmark is updated to
        target a non-existent data set.
        """

        _, _, benchmark, _, _, _ = commit_benchmark(db, False, " ")
        benchmark.test_set_ids = [" "]

        with pytest.raises(DataSetNotFoundError):

            update_and_compare_model(
                db,
                benchmark,
                BenchmarkCRUD.update,
                functools.partial(
                    BenchmarkCRUD.read,
                    project_id=benchmark.project_id,
                    study_id=benchmark.study_id,
                    optimization_id=benchmark.id,
                ),
                compare_benchmarks,
            )

    # def test_update_with_results(self, db: Session):
    #     """Test that a benchmark which has results uploaded can only be
    #     updated once the results have been deleted.
    #     """
    #
    #     project, study, optimization, _ = commit_optimization(db)
    #
    #     db.add(
    #         OptimizationResultCRUD.create(
    #             db, create_optimization_result(project.id, study.id, optimization.id)
    #         )
    #     )
    #     db.commit()
    #
    #     with pytest.raises(UnableToUpdateError):
    #         OptimizationCRUD.update(db, optimization)
    #
    #     # Delete the results and try again.
    #     OptimizationResultCRUD.delete(db, project.id, study.id, optimization.id)
    #     OptimizationCRUD.update(db, optimization)

    def test_update_not_found(self, db: Session):

        benchmark = create_benchmark(" ", " ", " ", [" "], None, " ")

        with pytest.raises(BenchmarkNotFoundError):
            BenchmarkCRUD.update(db, benchmark)
