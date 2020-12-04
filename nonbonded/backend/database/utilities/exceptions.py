import abc
from typing import Iterable

from fastapi import HTTPException


class ItemExistsError(HTTPException, abc.ABC):
    def __init__(self, detail: str):
        super(ItemExistsError, self).__init__(status_code=409, detail=detail)


class ItemNotFound(HTTPException, abc.ABC):
    def __init__(self, detail: str):
        super(ItemNotFound, self).__init__(status_code=404, detail=detail)


class UnableToCreateError(HTTPException, abc.ABC):
    def __init__(self, detail: str):
        super(UnableToCreateError, self).__init__(status_code=400, detail=detail)


class UnableToUpdateError(HTTPException, abc.ABC):
    def __init__(self, detail: str):
        super(UnableToUpdateError, self).__init__(status_code=400, detail=detail)


class UnableToDeleteError(HTTPException, abc.ABC):
    def __init__(self, detail: str):
        super(UnableToDeleteError, self).__init__(status_code=400, detail=detail)


class DataSetExistsError(ItemExistsError):
    def __init__(self, data_set_id):
        self.data_set_id = data_set_id

        super(DataSetExistsError, self).__init__(
            f"A data set with id={data_set_id} already exists."
        )


class DataSetNotFoundError(ItemNotFound):
    def __init__(self, data_set_id):
        self.data_set_id = data_set_id

        super(DataSetNotFoundError, self).__init__(
            f"The data base does not contain a data set with id={data_set_id}."
        )


class DataSetEntryNotFound(ItemNotFound):
    def __init__(self, detail: str):
        super(DataSetEntryNotFound, self).__init__(detail=detail)


class QCDataSetExistsError(ItemExistsError):
    def __init__(self, qc_data_set_id):
        self.qc_data_set_id = qc_data_set_id

        super(QCDataSetExistsError, self).__init__(
            f"A QC data set with id={qc_data_set_id} already exists."
        )


class QCDataSetNotFoundError(ItemNotFound):
    def __init__(self, qc_data_set_id):
        self.qc_data_set_id = qc_data_set_id

        super(QCDataSetNotFoundError, self).__init__(
            f"The database does not contain a QC data set with id={qc_data_set_id}."
        )


class BenchmarkExistsError(ItemExistsError):
    def __init__(self, project_id, study_id, benchmark_id):

        self.project_id = project_id
        self.study_id = study_id
        self.benchmark_id = benchmark_id

        super(BenchmarkExistsError, self).__init__(
            f"A benchmark with id={benchmark_id} and parent study "
            f"id={study_id} and parent project id={project_id} already "
            f"exists."
        )


class BenchmarkNotFoundError(ItemNotFound):
    def __init__(self, project_id, study_id, benchmark_id):

        self.project_id = project_id
        self.study_id = study_id
        self.benchmark_id = benchmark_id

        super(BenchmarkNotFoundError, self).__init__(
            f"The data base does not contain a benchmark with id={benchmark_id} "
            f"which is part of a study with id={study_id} and project with "
            f"id={project_id}."
        )


class BenchmarkResultExistsError(ItemExistsError):
    def __init__(self, project_id, study_id, benchmark_id):

        self.project_id = project_id
        self.study_id = study_id
        self.benchmark_id = benchmark_id

        super(BenchmarkResultExistsError, self).__init__(
            f"A result belonging to a benchmark with id={benchmark_id} and parent study "
            f"id={study_id} and parent project id={project_id} already exists."
        )


class BenchmarkResultNotFoundError(ItemNotFound):
    def __init__(self, project_id, study_id, benchmark_id):

        self.project_id = project_id
        self.study_id = study_id
        self.benchmark_id = benchmark_id

        super(BenchmarkResultNotFoundError, self).__init__(
            f"The data base does not contain a result for the benchmark with "
            f"id={benchmark_id} which is part of a study with id={study_id} and "
            f"project with id={project_id}."
        )


class OptimizationExistsError(ItemExistsError):
    def __init__(self, project_id, study_id, optimization_id):

        self.project_id = project_id
        self.study_id = study_id
        self.optimization_id = optimization_id

        super(OptimizationExistsError, self).__init__(
            f"An optimization with id={optimization_id} and parent study "
            f"id={study_id} and parent project id={project_id} already "
            f"exists."
        )


class OptimizationNotFoundError(ItemNotFound):
    def __init__(self, project_id, study_id, optimization_id):

        self.project_id = project_id
        self.study_id = study_id
        self.optimization_id = optimization_id

        super(OptimizationNotFoundError, self).__init__(
            f"The data base does not contain an optimization with id={optimization_id} "
            f"which is part of a study with id={study_id} and project with "
            f"id={project_id}."
        )


class TargetNotFoundError(ItemNotFound):
    def __init__(
        self,
        project_id: str,
        study_id: str,
        optimization_id: str,
        target_ids: Iterable[str],
    ):

        self.project_id = project_id
        self.study_id = study_id
        self.optimization_id = optimization_id

        self.target_ids = target_ids

        target_id_string = ", ".join(target_ids)

        super(TargetNotFoundError, self).__init__(
            f"Results were provided for targets with ids={target_id_string} however the "
            f"corresponding optimization with id={optimization_id} (study id={study_id} "
            f"and project id={project_id}) contains no such targets."
        )


class TargetResultNotFoundError(ItemNotFound):
    def __init__(
        self,
        project_id: str,
        study_id: str,
        optimization_id: str,
        target_ids: Iterable[str],
    ):

        self.project_id = project_id
        self.study_id = study_id
        self.optimization_id = optimization_id

        self.target_ids = target_ids

        target_id_string = ", ".join(target_ids)

        super(TargetResultNotFoundError, self).__init__(
            f"No results were found for the {target_id_string} targets which are "
            f"required for the optimization with id={optimization_id} (study id="
            f"{study_id} and project id={project_id})."
        )


class TargetResultTypeError(ItemNotFound):
    def __init__(
        self,
        project_id: str,
        study_id: str,
        optimization_id: str,
        target_id: str,
        target_type,
        expected_type,
    ):

        self.project_id = project_id
        self.study_id = study_id
        self.optimization_id = optimization_id

        self.target_id = target_id

        self.target_type = target_type
        self.expected_type = expected_type

        super(TargetResultTypeError, self).__init__(
            f"A result with type {target_type.__name__} was provided for "
            f"target={target_id}, however a type of {expected_type.__name__} was "
            f"expected."
        )


class OptimizationResultExistsError(ItemExistsError):
    def __init__(self, project_id, study_id, optimization_id):

        self.project_id = project_id
        self.study_id = study_id
        self.optimization_id = optimization_id

        super(OptimizationResultExistsError, self).__init__(
            f"A result belonging to a optimization with id={optimization_id} and parent "
            f"study id={study_id} and parent project id={project_id} already exists."
        )


class OptimizationResultNotFoundError(ItemNotFound):
    def __init__(self, project_id, study_id, optimization_id):

        self.project_id = project_id
        self.study_id = study_id
        self.optimization_id = optimization_id

        super(OptimizationResultNotFoundError, self).__init__(
            f"The data base does not contain a result for the optimization with "
            f"id={optimization_id} which is part of a study with id={study_id} and "
            f"project with id={project_id}."
        )


class StudyExistsError(ItemExistsError):
    def __init__(self, project_id, study_id):

        self.project_id = project_id
        self.study_id = study_id

        super(StudyExistsError, self).__init__(
            f"A study with id={study_id} and parent project id={project_id} already "
            f"exists."
        )


class StudyNotFoundError(ItemNotFound):
    def __init__(self, project_id, study_id):

        self.project_id = project_id
        self.study_id = study_id

        super(StudyNotFoundError, self).__init__(
            f"The data base does not contain a study with id={study_id} "
            f"which is part of a project with id={project_id}."
        )


class ProjectExistsError(ItemExistsError):
    def __init__(self, project_id):
        self.project_id = project_id

        super(ProjectExistsError, self).__init__(
            f"A project with id={project_id} already exists."
        )


class ProjectNotFoundError(ItemNotFound):
    def __init__(self, project_id):
        self.project_id = project_id

        super(ProjectNotFoundError, self).__init__(
            f"The data base does not contain a project with id={project_id}."
        )


class ForceFieldExistsError(ItemExistsError):
    def __init__(self, project_id, study_id, optimization_id):

        super(ForceFieldExistsError, self).__init__(
            f"The database already contains the exact same force field "
            f"as the refit one being uploaded. This should likely never "
            f"happen (project_id={project_id}, study_id={study_id}, "
            f"optimization_id={optimization_id})."
        )
