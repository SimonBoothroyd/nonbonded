from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.models import results


class BenchmarkResultsCRUD:
    @staticmethod
    def create(
        db: Session, benchmark_results: results.BenchmarkResults
    ) -> models.BenchmarkResults:

        db_statistic_data = []
        db_comparison_data = []

        for property_result in benchmark_results.property_results:

            for force_field_result in property_result.force_field_results:

                statistic_data = force_field_result.statistic_data
                scatter_data = force_field_result.scatter_data

                for statistic_type in statistic_data.values:

                    db_statistic = models.StatisticData(
                        property_type=property_result.property_type,
                        n_components=property_result.n_components,
                        force_field_name=force_field_result.force_field_name,
                        statistic_type=statistic_type,
                        value=statistic_data.values[statistic_type],
                        lower_ci=statistic_data.confidence_intervals[statistic_type][0],
                        upper_ci=statistic_data.confidence_intervals[statistic_type][1],
                    )

                    db_statistic_data.append(db_statistic)

                for series in scatter_data.series:

                    for x, y, metadata in zip(series.x, series.y, series.metadata):

                        db_comparison = models.ComparisonData(
                            property_type=property_result.property_type,
                            n_components=property_result.n_components,
                            force_field_name=force_field_result.force_field_name,
                            name=series.name,
                            x=x,
                            y=y,
                            meta_data=metadata,
                        )

                        db_comparison_data.append(db_comparison)

        # noinspection PyTypeChecker
        db_benchmark_results = models.BenchmarkResults(
            project_identifier=benchmark_results.project_identifier,
            study_identifier=benchmark_results.study_identifier,
            comparison_data=db_comparison_data,
            statistic_data=db_statistic_data,
        )

        db.add(db_benchmark_results)
        db.commit()
        db.refresh(db_benchmark_results)

        return db_benchmark_results

    @staticmethod
    def read_by_identifiers(
        db: Session, project_identifier: Optional[str], study_identifier: Optional[str]
    ):

        db_results = db.query(models.BenchmarkResults)

        if project_identifier is not None:
            db_results = db_results.filter_by(project_identifier=project_identifier)
        if study_identifier is not None:
            db_results = db_results.filter_by(study_identifier=study_identifier)

        return [
            BenchmarkResultsCRUD.db_to_model(db_result)
            for db_result in db_results.all()
        ]

    @staticmethod
    def db_to_model(db_result: models.BenchmarkResults) -> results.BenchmarkResults:

        x = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        y = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        metadata = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        # noinspection PyTypeChecker
        for data in db_result.comparison_data:

            x[(data.property_type, data.n_components)][data.force_field_name][
                data.name
            ].append(data.x)
            y[(data.property_type, data.n_components)][data.force_field_name][
                data.name
            ].append(data.y)

            metadata[(data.property_type, data.n_components)][data.force_field_name][
                data.name
            ].append(data.meta_data)

        value = defaultdict(lambda: defaultdict(dict))
        ci = defaultdict(lambda: defaultdict(dict))

        # noinspection PyTypeChecker
        for data in db_result.statistic_data:

            value[(data.property_type, data.n_components)][data.force_field_name][
                data.statistic_type
            ] = data.value
            ci[(data.property_type, data.n_components)][data.force_field_name][
                data.statistic_type
            ] = (data.lower_ci, data.upper_ci)

        property_results = []

        for property_tuple in x:

            force_field_results = []

            for force_field_name in x[property_tuple]:

                scatter_data = []

                for name in x[property_tuple][force_field_name]:

                    scatter_series = results.ScatterSeries(
                        name=name,
                        x=x[property_tuple][force_field_name][name],
                        y=y[property_tuple][force_field_name][name],
                        metadata=metadata[property_tuple][force_field_name][name],
                    )

                    scatter_data.append(scatter_series)

                scatter_data = results.ScatterData(series=scatter_data)

                statistic_data = results.StatisticData(
                    values=value[property_tuple][force_field_name],
                    confidence_intervals=ci[property_tuple][force_field_name],
                )

                force_field_result = results.ForceFieldResults(
                    force_field_name=force_field_name,
                    scatter_data=scatter_data,
                    statistic_data=statistic_data,
                )

                force_field_results.append(force_field_result)

            property_result = results.PropertyResults(
                property_type=property_tuple[0],
                n_components=property_tuple[1],
                force_field_results=force_field_results,
            )
            property_results.append(property_result)

        benchmark_results = results.BenchmarkResults(
            project_identifier=db_result.project_identifier,
            study_identifier=db_result.study_identifier,
            property_results=property_results,
        )

        return benchmark_results


class OptimizationResultCRUD:
    @staticmethod
    def read_by_identifiers(
        db: Session,
        project_identifier: Optional[str],
        study_identifier: Optional[str],
        optimization_identifier: Optional[str],
    ):

        db_results = db.query(models.OptimizationResult)

        if project_identifier is not None:
            db_results = db_results.filter_by(project_identifier=project_identifier)
        if study_identifier is not None:
            db_results = db_results.filter_by(study_identifier=study_identifier)
        if optimization_identifier is not None:
            db_results = db_results.filter_by(
                optimization_identifier=optimization_identifier
            )

        return [
            OptimizationResultCRUD.db_to_model(db_result)
            for db_result in db_results.all()
        ]

    @staticmethod
    def create(
        db: Session, result: results.OptimizationResult
    ) -> models.OptimizationResult:

        # noinspection PyTypeChecker
        db_result = models.OptimizationResult(
            project_identifier=result.project_identifier,
            study_identifier=result.study_identifier,
            optimization_identifier=result.optimization_identifier,
            objective_function=[
                models.ObjectiveFunctionData(iteration=x, value=y)
                for x, y in result.objective_function.items()
            ],
        )

        db.add(db_result)
        db.commit()
        db.refresh(db_result)

        return db_result

    @staticmethod
    def db_to_model(db_result: models.OptimizationResult) -> results.OptimizationResult:

        # noinspection PyTypeChecker
        result = results.OptimizationResult(
            project_identifier=db_result.project_identifier,
            study_identifier=db_result.study_identifier,
            optimization_identifier=db_result.optimization_identifier,
            objective_function={
                data.iteration: data.value for data in db_result.objective_function
            },
        )

        return result
