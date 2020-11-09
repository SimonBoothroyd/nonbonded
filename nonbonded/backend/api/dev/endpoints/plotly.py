import logging
from typing import Dict, List

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
from nonbonded.library.plotting.plotly.benchmark import (
    plot_overall_statistics,
    plot_scatter_results,
)
from nonbonded.library.plotting.plotly.optimization import plot_objective_per_iteration
from nonbonded.library.statistics.statistics import StatisticType

logger = logging.getLogger(__name__)
router = APIRouter()


class SubStudyId(BaseModel):

    project_id: str
    study_id: str
    sub_study_id: str


class PlotlyEndpoints:
    @staticmethod
    @router.post("/optimizations/objective")
    async def post_objective_function(
        sub_study_ids: List[SubStudyId],
        db: Session = Depends(depends.get_db),
    ) -> Figure:

        optimizations = [
            OptimizationCRUD.read(db, **sub_study_id.dict())
            for sub_study_id in sub_study_ids
        ]
        results = [
            OptimizationResultCRUD.read(db, **sub_study_id.dict())
            for sub_study_id in sub_study_ids
        ]

        return plot_objective_per_iteration(optimizations, results)

    @staticmethod
    @router.post("/benchmarks/statistics/{statistic_type}")
    async def post_overall_statistics(
        sub_study_ids: List[SubStudyId],
        statistic_type: Literal["rmse"],
        db: Session = Depends(depends.get_db),
    ) -> Figure:
        benchmarks = [
            BenchmarkCRUD.read(db, **sub_study_id.dict())
            for sub_study_id in sub_study_ids
        ]
        results = [
            BenchmarkResultCRUD.read(db, **sub_study_id.dict())
            for sub_study_id in sub_study_ids
        ]

        return plot_overall_statistics(
            benchmarks, results, StatisticType[statistic_type.upper()]
        )

    @staticmethod
    @router.post("/benchmarks/scatter")
    async def post_scatter_results(
        sub_study_ids: List[SubStudyId],
        db: Session = Depends(depends.get_db),
    ) -> Dict[str, Figure]:

        benchmarks = [
            BenchmarkCRUD.read(db, **sub_study_id.dict())
            for sub_study_id in sub_study_ids
        ]
        results = [
            BenchmarkResultCRUD.read(db, **sub_study_id.dict())
            for sub_study_id in sub_study_ids
        ]

        data_set_ids = {
            test_set_id
            for benchmark in benchmarks
            for test_set_id in benchmark.test_set_ids
        }
        data_sets = [DataSetCRUD.read(db, data_set_id) for data_set_id in data_set_ids]

        return plot_scatter_results(benchmarks, results, data_sets)
