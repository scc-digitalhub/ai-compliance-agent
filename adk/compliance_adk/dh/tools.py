"""Tools for managing compliance-related extensions of the DH platform entities.
"""


from ..contracts.results import ComplianceContextOut, DataComplianceOut, ModelComplianceOut


def get_project_extension(project: str, extension_kind: str) -> dict:
    """Retrieve the compliance-related extension for a given project."""
    print(f"Retrieving project extension for project: {project}, extension kind: {extension_kind}")
    # Placeholder implementation, replace with actual logic
    return {}

def get_entity_extension(entity: str, entity_kind: str, extension_kind: str) -> dict:
    """Retrieve the compliance-related extension for a given entity."""
    print(f"Retrieving entity extension for entity: {entity}, entity kind: {entity_kind}, extension kind: {extension_kind}")
    # Placeholder implementation, replace with actual logic
    return {}

def save_project_extension(project: str, extension_kind: str, extension: dict) -> None:
    """Save the compliance-related extension for a given project."""
    print(f"Saving project extension for project: {project}, extension kind: {extension_kind}, extension: {extension}")
    # Placeholder implementation, replace with actual logic
    pass

def save_entity_extension(entity: str, entity_kind: str, extension_kind: str, extension: dict) -> None:
    """Save the compliance-related extension for a given entity."""
    print(f"Saving entity extension for entity: {entity}, entity kind: {entity_kind}, extension kind: {extension_kind}, extension: {extension}")
    # Placeholder implementation, replace with actual logic
    pass    

def get_extension_schema(extension_kind: str) -> dict:
    """Retrieve the JSON schema for a given extension kind."""
    print(f"Retrieving extension schema for extension kind: {extension_kind}")
    # Placeholder implementation, replace with actual logic
    if extension_kind == 'project-compliance':
        return ComplianceContextOut.model_json_schema()
    if extension_kind == 'data-compliance':
        return DataComplianceOut.model_json_schema()
    if extension_kind == 'model-compliance':
        return ModelComplianceOut.model_json_schema()
    return {}