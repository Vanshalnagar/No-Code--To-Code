# parser/loader.py
import json
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

def load_raw_json(json_str: str) -> Dict[str, Any]:
    """Load raw JSON from automation platforms"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {str(e)}")
        raise ValueError(f"Invalid JSON: {str(e)}") from e

def preprocess_n8n_json(data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Convert n8n JSON to normalized structure"""
    # Create mappings
    id_to_node = {node['id']: node for node in data['nodes']}
    name_to_id = {node['name']: node['id'] for node in data['nodes'] if 'name' in node}
    
    # Build connection map
    next_map = {node_id: [] for node_id in id_to_node}
    
    # Process connections
    for source_name, outputs in data.get('connections', {}).items():
        if source_name not in name_to_id:
            logger.warning(f"Connection source '{source_name}' not found in nodes")
            continue
            
        source_id = name_to_id[source_name]
        for output_group in outputs.values():
            for connection_list in output_group:
                for connection in connection_list:
                    target_name = connection['node']
                    if target_name not in name_to_id:
                        logger.warning(f"Connection target '{target_name}' not found in nodes")
                        continue
                    next_map[source_id].append(name_to_id[target_name])
    
    # Build normalized workflow
    normalized_workflow = {
        "name": data.get('name', 'Unnamed Workflow'),
        "nodes": {}
    }
    
    for node_id, node in id_to_node.items():
        # Convert type_version to string
        type_version = node.get('typeVersion', '1.0')
        if not isinstance(type_version, str):
            type_version = str(type_version)
        
        normalized_workflow['nodes'][node_id] = {
            "id": node_id,
            "name": node.get('name'),
            "type": node['type'],
            "type_version": type_version,
            "config": node.get('parameters', {}),
            "next": next_map.get(node_id, []),
            "disabled": node.get('disabled', False),
            "credentials": node.get('credentials'),
            "position": node.get('position'),
            "webhookId": node.get('webhookId'),
        }
    
    return normalized_workflow, id_to_node
