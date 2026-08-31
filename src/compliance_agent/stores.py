"""Shared EntityStore singletons — imported by both api/crud.py and api/main.py."""
from config import settings
from store import EntityStore

projects = EntityStore(settings.data_path, "projects")
datasets = EntityStore(settings.data_path, "datasets")
models   = EntityStore(settings.data_path, "models")
