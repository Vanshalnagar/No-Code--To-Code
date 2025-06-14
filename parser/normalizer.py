# parser/normalizer.py
from .models import ASTNode, WorkflowAST
import logging

logger = logging.getLogger(__name__)

def parse_to_ast(raw_workflow: dict) -> WorkflowAST:
    ast_nodes = {}
    
    for node_id, raw_node in raw_workflow['nodes'].items():
        try:
            ast_node = ASTNode(
                id=node_id,
                name=raw_node.get('name'),
                type=raw_node['type'],
                type_version=raw_node.get('type_version'),
                config=raw_node.get('config', {}),
                next=raw_node.get('next', []),  # Set the next field
                disabled=raw_node.get('disabled', False),
                position=raw_node.get('position'),
                webhook_id=raw_node.get('webhookId'),
            )
            ast_nodes[node_id] = ast_node
        except Exception as e:
            logger.error(f"Failed to create ASTNode for {node_id}: {str(e)}")
            raise
    
    return WorkflowAST(
        name=raw_workflow.get('name', 'Unnamed Workflow'),
        nodes=ast_nodes
    )
