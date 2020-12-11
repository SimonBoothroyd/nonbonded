import logging
from typing import Dict, List, Tuple

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing_extensions import Literal

from nonbonded.backend.api import depends
from nonbonded.backend.database.crud.datasets import DataSetCRUD
from nonbonded.backend.database.crud.projects import BenchmarkCRUD, OptimizationCRUD
from nonbonded.backend.database.crud.results import (
    BenchmarkResultCRUD,
    OptimizationResultCRUD,
)
from nonbonded.library.models.plotly import Figure
from nonbonded.library.models.projects import Benchmark, Optimization
from nonbonded.library.models.results import BenchmarkResult, OptimizationResult
from nonbonded.library.plotting.plotly.benchmark import (
    plot_overall_statistics,
    plot_scatter_results,
)
from nonbonded.library.plotting.plotly.optimization import (
    plot_objective_per_iteration,
    plot_target_rmse,
)
from nonbonded.library.statistics.statistics import StatisticType

logger = logging.getLogger(__name__)
router = APIRouter()


class SubStudyId(BaseModel):

    project_id: str
    study_id: str
    sub_study_id: str


class PlotlyEndpoints:
    @staticmethod
    def _get_optimization_results(
        db: Session, project_id: str, study_id: str
    ) -> Tuple[List[Optimization], List[OptimizationResult]]:

        optimizations = OptimizationCRUD.read_all(
            db, project_id=project_id, study_id=study_id
        )
        results = [
            OptimizationResultCRUD.read(
                db,
                project_id=project_id,
                study_id=study_id,
                sub_study_id=optimization.id,
            )
            for optimization in optimizations
        ]

        return optimizations, results

    @staticmethod
    def _get_benchmark_results(
        db: Session, project_id: str, study_id: str
    ) -> Tuple[List[Benchmark], List[BenchmarkResult]]:

        benchmarks = BenchmarkCRUD.read_all(
            db, project_id=project_id, study_id=study_id
        )
        results = [
            BenchmarkResultCRUD.read(
                db,
                project_id=project_id,
                study_id=study_id,
                sub_study_id=benchmark.id,
            )
            for benchmark in benchmarks
        ]

        return benchmarks, results

    @staticmethod
    @router.get("/optimizations/objective")
    async def get_optimization_objective_function(
        projectid: str,
        studyid: str,
        db: Session = Depends(depends.get_db),
    ) -> Figure:

        return plot_objective_per_iteration(
            *PlotlyEndpoints._get_optimization_results(db, projectid, studyid)
        )

    @staticmethod
    @router.get("/optimizations/rmse")
    async def get_optimization_rmse(
        projectid: str,
        studyid: str,
        db: Session = Depends(depends.get_db),
    ) -> Dict[str, Dict[str, Dict[str, Figure]]]:

        optimizations, results = PlotlyEndpoints._get_optimization_results(
            db, projectid, studyid
        )

        figures = {}

        for optimization, result in zip(optimizations, results):

            if result is None or len(result.target_results) == 0:
                continue

            targets_by_id = {target.id: target for target in optimization.targets}
            final_iteration = sorted(result.target_results)[-1]

            figures[optimization.id] = {
                target_id: plot_target_rmse(
                    [targets_by_id[target_id], targets_by_id[target_id]],
                    [initial_result, result.target_results[final_iteration][target_id]],
                    ["Initial", "Final"],
                )
                for target_id, initial_result in result.target_results[0].items()
            }

        return figures

    @staticmethod
    @router.get("/benchmarks/statistics/{statistic_type}")
    async def get_overall_benchmark_statistics(
        projectid: str,
        studyid: str,
        statistic_type: Literal["rmse"],
        db: Session = Depends(depends.get_db),
    ) -> Figure:

        return plot_overall_statistics(
            *PlotlyEndpoints._get_benchmark_results(db, projectid, studyid),
            StatisticType[statistic_type.upper()]
        )

    @staticmethod
    @router.get("/benchmarks/scatter")
    async def get_benchmark_scatter_results(
        projectid: str,
        studyid: str,
        db: Session = Depends(depends.get_db),
    ) -> Dict[str, Figure]:

        benchmarks, results = PlotlyEndpoints._get_benchmark_results(
            db, projectid, studyid
        )

        data_set_ids = {
            test_set_id
            for benchmark in benchmarks
            for test_set_id in benchmark.test_set_ids
        }
        data_sets = [DataSetCRUD.read(db, data_set_id) for data_set_id in data_set_ids]

        return plot_scatter_results(benchmarks, results, data_sets)
