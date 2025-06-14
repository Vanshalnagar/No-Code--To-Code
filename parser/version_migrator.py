# parser/version_migrator.py
import logging
from typing import Dict, Callable, Any

logger = logging.getLogger(__name__)

MigrationFunction = Callable[[Dict[str, Any]], Dict[str, Any]]
MIGRATION_REGISTRY: Dict[str, MigrationFunction] = {}

def register_migration(version: str):
    def wrapper(fn: MigrationFunction):
        MIGRATION_REGISTRY[version] = fn
        return fn
    return wrapper

@register_migration("0.9")
def migrate_from_0_9(node: Dict[str, Any]) -> Dict[str, Any]:
    if node.get("type") == "request":
        node["type"] = "httpRequest"
    node["type_version"] = "1.0"
    logger.info(f"Migrated node {node.get('id')} from v0.9 to v1.0")
    return node

def migrate_node_schema(raw_node: Dict[str, Any]) -> Dict[str, Any]:
    version = raw_node.get("type_version", "1.0")
    if version in MIGRATION_REGISTRY:
        return MIGRATION_REGISTRY[version](raw_node)
    return raw_node

def migrate_workflow_schema(raw_workflow: Dict[str, Any]) -> Dict[str, Any]:
    if "nodes" in raw_workflow:
        for node_id, node_data in raw_workflow["nodes"].items():
            raw_workflow["nodes"][node_id] = migrate_node_schema(node_data)
    return raw_workflow
