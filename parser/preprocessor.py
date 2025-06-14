# parser/preprocessor.py
from typing import Dict, Any, List

def transform_n8n_to_raw_workflow(n8n_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms the native n8n JSON structure into the format
    expected by the RawWorkflow Pydantic model.

    - Converts the 'nodes' list to a dictionary keyed by node ID.
    - Parses the 'connections' object to populate the 'next' field for each node.
    """
    raw_workflow = {
        "name": n8n_json.get("name"),
        "nodes": {node["id"]: node for node in n8n_json.get("nodes", [])}
    }

    # Map node names to IDs for easy lookup from the connections object
    name_to_id_map = {node["name"]: node["id"] for node in raw_workflow["nodes"].values()}

    connections = n8n_json.get("connections", {})
    for source_node_name, outputs in connections.items():
        source_node_id = name_to_id_map.get(source_node_name)
        if not source_node_id:
            continue

        source_node = raw_workflow["nodes"].get(source_node_id)
        if not source_node:
            continue
        
        # Initialize 'next' if it doesn't exist
        if "next" not in source_node:
            source_node["next"] = []

        # Each output can connect to multiple target nodes
        for output in outputs.values():
            for connection_details in output:
                target_node_name = connection_details.get("node")
                target_node_id = name_to_id_map.get(target_node_name)
                if target_node_id and target_node_id not in source_node["next"]:
                    source_node["next"].append(target_node_id)

    # Rename 'parameters' to 'config' to match the RawNode model
    for node in raw_workflow["nodes"].values():
        if "parameters" in node:
            node["config"] = node.pop("parameters")
        else:
            node["config"] = {} # Ensure config key exists
        
        # Ensure 'typeVersion' is a string
        if "typeVersion" in node:
            node["type_version"] = str(node.pop("typeVersion"))

    return raw_workflow
