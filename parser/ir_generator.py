# parser/ir_generator.py
from .models import IRGraph, IREdge, WorkflowAST
import logging

logger = logging.getLogger(__name__)

def generate_ir(ast: WorkflowAST) -> IRGraph:
    ir_nodes = {}
    ir_edges = []
    
    for node_id, ast_node in ast.nodes.items():
        ir_nodes[node_id] = {
            "id": node_id,
            "type": ast_node.type,
            "name": ast_node.name,
            "resolved_config": ast_node.resolved_config,
            "runtime_env": ast_node.runtime_env.dict() if ast_node.runtime_env else {},
            "metadata": ast_node.metadata.dict() if ast_node.metadata else {},
            "credentials": ast_node.credentials,
            "inputs": ast_node.inputs,
            "position": ast_node.position,
            "webhook_id": ast_node.webhook_id,
        }
        
        for conn in ast_node.connections:
            ir_edges.append(IREdge(
                from_node=node_id,
                to_node=conn.id
            ))
    
    return IRGraph(
        name=ast.name,
        nodes=ir_nodes,
        edges=ir_edges
    )
