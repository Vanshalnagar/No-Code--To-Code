# parser/metadata_enricher.py
from .models import RuntimeEnv, NodeMetadata, ASTNode
from .plugin_loader import resolve_credentials
import logging

logger = logging.getLogger(__name__)

def enrich_metadata(ast_nodes: dict, raw_nodes: dict) -> None:
    for node_id, ast_node in ast_nodes.items():
        raw_node = raw_nodes.get(node_id)
        if not raw_node:
            logger.warning(f"No raw data for node {node_id}")
            continue
            
        try:
            # Credential resolution
            if 'credentials' in raw_node:
                ast_node.credentials = resolve_credentials(raw_node['credentials'])
            
            # Runtime environment
            env = raw_node.get('env', {})
            ast_node.runtime_env = RuntimeEnv(**env) if env else None
            
            # Metadata
            ast_node.metadata = NodeMetadata(
                notes=raw_node.get('notes'),
                tags=raw_node.get('tags', []),
                created_by=raw_node.get('createdBy'),
                created_at=raw_node.get('createdAt'),
                last_modified=raw_node.get('lastModified'),
                original_raw_node=raw_node,
            )
            
            # LLM hints
            node_type = ast_node.type.lower()
            if any(kw in node_type for kw in ["http", "fetch", "api"]):
                ast_node.metadata.llm_hint = "IO_BOUND"
            elif any(kw in node_type for kw in ["delay", "sleep", "wait"]):
                ast_node.metadata.llm_hint = "TIME_BLOCKING"
            elif any(kw in node_type for kw in ["code", "function", "script"]):
                ast_node.metadata.llm_hint = "CPU_BOUND"
            else:
                ast_node.metadata.llm_hint = "GENERAL"
                
        except Exception as e:
            logger.error(f"Metadata enrichment failed for {node_id}: {str(e)}")
            raise
