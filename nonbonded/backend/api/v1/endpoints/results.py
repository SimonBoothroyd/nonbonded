import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from requests import Session

from nonbonded.backend.api import depends
from nonbonded.backend.database.crud.results import (
    BenchmarkResultsCRUD,
    OptimizationResultCRUD,
)
from nonbonded.library.models.results import (
    BenchmarkResults,
    BenchmarkResultsCollection,
    OptimizationResult,
    OptimizationResultCollection,
)

router = APIRouter()

PROJECT_DIRECTORY = os.path.join("rest", "projects")


@router.get("/benchmark", response_model=BenchmarkResultsCollection)
async def get_benchmark_results(
    project_id: Optional[str] = None,
    study_id: Optional[str] = None,
    db: Session = Depends(depends.get_db),
):

    results = BenchmarkResultsCRUD.read_by_identifiers(db, project_id, study_id)
    return {"results": results}


@router.post("/benchmark")
async def post_benchmark_results(
    benchmark_results: BenchmarkResults, db: Session = Depends(depends.get_db)
):

    db_results = BenchmarkResultsCRUD.read_by_identifiers(
        db, benchmark_results.project_identifier, benchmark_results.study_identifier
    )

    if db_results:

        raise HTTPException(status_code=400, detail="Benchmark results already posted")

    return BenchmarkResultsCRUD.create(db=db, benchmark_results=benchmark_results)


@router.get("/optimization", response_model=OptimizationResultCollection)
async def get_optimization_results(
    project_id: Optional[str] = None,
    study_id: Optional[str] = None,
    optimization_id: Optional[str] = None,
    db: Session = Depends(depends.get_db),
):

    results = OptimizationResultCRUD.read_by_identifiers(
        db, project_id, study_id, optimization_id
    )

    return {"results": results}


@router.post("/optimization")
async def post_optimization_results(
    optimization_result: OptimizationResult, db: Session = Depends(depends.get_db)
):

    db_results = OptimizationResultCRUD.read_by_identifiers(
        db,
        optimization_result.project_identifier,
        optimization_result.study_identifier,
        optimization_result.optimization_identifier,
    )

    if db_results:

        raise HTTPException(
            status_code=400, detail="Optimization results already posted."
        )

    return OptimizationResultCRUD.create(db=db, result=optimization_result)
