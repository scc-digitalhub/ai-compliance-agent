"""Session-state keys under which the coordinator keeps the analyses of a conversation."""

PROJECT_KEY = "analysis_project"
CONTEXT_KEY = "analysis_project_context"
DATASETS_KEY = "analysis_datasets"  # {dataset name: DataComplianceOut}
MODELS_KEY = "analysis_models"  # {model name: ModelComplianceOut}
ENTITIES_KEY = "dh_entities"  # {"dataset" | "model": {entity name: details retrieved from the DH platform}}
