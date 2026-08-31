"""CRUD endpoints for project, dataset, and model entities."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.models import DatasetInput, ModelInput, ProjectInput
import stores

router = APIRouter(prefix="/entities", tags=["entities"])

_projects = stores.projects
_datasets = stores.datasets
_models   = stores.models


def _or_404(entity: dict | None, kind: str, entity_id: str) -> dict:
    if entity is None:
        raise HTTPException(status_code=404, detail=f"{kind} '{entity_id}' not found")
    return entity


# ── Projects ──────────────────────────────────────────────────────────────────

@router.get("/projects", summary="List all projects")
def list_projects() -> list[dict]:
    return _projects.list_all()


@router.post("/projects", status_code=201, summary="Create a project")
def create_project(project: ProjectInput) -> dict:
    return _projects.create(project.model_dump())


@router.get("/projects/{project_id}", summary="Get a project by ID")
def get_project(project_id: str) -> dict:
    return _or_404(_projects.get(project_id), "Project", project_id)


@router.put("/projects/{project_id}", summary="Replace a project")
def update_project(project_id: str, project: ProjectInput) -> dict:
    return _or_404(_projects.update(project_id, project.model_dump()), "Project", project_id)


@router.delete("/projects/{project_id}", status_code=204, summary="Delete a project")
def delete_project(project_id: str) -> None:
    if not _projects.delete(project_id):
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")


# ── Datasets ──────────────────────────────────────────────────────────────────

@router.get("/datasets", summary="List all datasets")
def list_datasets() -> list[dict]:
    return _datasets.list_all()


@router.post("/datasets", status_code=201, summary="Create a dataset")
def create_dataset(dataset: DatasetInput) -> dict:
    return _datasets.create(dataset.model_dump())


@router.get("/datasets/{dataset_id}", summary="Get a dataset by ID")
def get_dataset(dataset_id: str) -> dict:
    return _or_404(_datasets.get(dataset_id), "Dataset", dataset_id)


@router.put("/datasets/{dataset_id}", summary="Replace a dataset")
def update_dataset(dataset_id: str, dataset: DatasetInput) -> dict:
    return _or_404(_datasets.update(dataset_id, dataset.model_dump()), "Dataset", dataset_id)


@router.delete("/datasets/{dataset_id}", status_code=204, summary="Delete a dataset")
def delete_dataset(dataset_id: str) -> None:
    if not _datasets.delete(dataset_id):
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")


# ── Models ────────────────────────────────────────────────────────────────────

@router.get("/models", summary="List all models")
def list_models() -> list[dict]:
    return _models.list_all()


@router.post("/models", status_code=201, summary="Create a model")
def create_model(model: ModelInput) -> dict:
    return _models.create(model.model_dump())


@router.get("/models/{model_id}", summary="Get a model by ID")
def get_model(model_id: str) -> dict:
    return _or_404(_models.get(model_id), "Model", model_id)


@router.put("/models/{model_id}", summary="Replace a model")
def update_model(model_id: str, model: ModelInput) -> dict:
    return _or_404(_models.update(model_id, model.model_dump()), "Model", model_id)


@router.delete("/models/{model_id}", status_code=204, summary="Delete a model")
def delete_model(model_id: str) -> None:
    if not _models.delete(model_id):
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
