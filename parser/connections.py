# parser/connections.py
from .models import WorkflowAST
import logging

logger = logging.getLogger(__name__)

def build_connections(ast: WorkflowAST) -> None:
    """Build DAG connections between AST nodes"""
    # First pass: create ID to node mapping
    node_map = {node_id: node for node_id, node in ast.nodes.items()}
    
    # Second pass: build connections
    for node_id, ast_node in ast.nodes.items():
        if ast_node.disabled:
            continue
            
        # Use the next field which contains node IDs
        for next_id in ast_node.next:
            if next_id not in node_map:
                logger.warning(f"Node '{node_id}' points to missing node '{next_id}'")
                continue
                
            target_node = node_map[next_id]
            if target_node not in ast_node.connections:
                ast_node.connections.append(target_node)
                
            # Add reverse reference for static analysis
            if ast_node.id not in target_node.inputs:
                target_node.inputs.append(ast_node.id)
