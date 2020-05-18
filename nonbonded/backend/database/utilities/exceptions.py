import abc

from fastapi import HTTPException


class ItemExistsError(HTTPException, abc.ABC):
    def __init__(self, detail: str):
        super(ItemExistsError, self).__init__(status_code=409, detail=detail)


class ItemNotFound(HTTPException, abc.ABC):
    def __init__(self, detail: str):
        super(ItemNotFound, self).__init__(status_code=404, detail=detail)


class UnableToUpdateError(HTTPException, abc.ABC):
    def __init__(self, detail: str):
        super(UnableToUpdateError, self).__init__(status_code=400, detail=detail)


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


class DataSetInUseError(HTTPException):
    def __init__(self, data_set_id):

        self.data_set_id = data_set_id

        super(DataSetInUseError, self).__init__(
            status_code=400,
            detail=f"The data set with id={data_set_id} is still being used in a "
            f"project and so cannot be deleted.",
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
            f"The data base does not contain an benchmark with id={benchmark_id} "
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


class RefitForceFieldExistsError(ItemExistsError):
    def __init__(self, project_id, study_id, optimization_id):

        self.project_id = project_id
        self.study_id = study_id
        self.optimization_id = optimization_id

        super(RefitForceFieldExistsError, self).__init__(
            f"The optimization with id={optimization_id} which is part of a study with "
            f"id={study_id} and project with id={project_id} already has a registered "
            f"refit force field."
        )


class RefitForceFieldNotFoundError(ItemNotFound):
    def __init__(self, project_id, study_id, optimization_id):

        self.project_id = project_id
        self.study_id = study_id
        self.optimization_id = optimization_id

        super(RefitForceFieldNotFoundError, self).__init__(
            f"The data base does not contain an a force which was refit as part of the "
            f"optimization with id={optimization_id} which is part of a study with "
            f"id={study_id} and project with id={project_id}."
        )
