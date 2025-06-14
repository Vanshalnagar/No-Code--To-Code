# parser/pipeline.py
import asyncio
import logging
from .loader import load_raw_json, preprocess_n8n_json
from .validator import validate_structure
from .normalizer import parse_to_ast
from .connections import build_connections
from .metadata_enricher import enrich_metadata
from .interpreter import interpret_node, build_safe_node
from .static_analyzer import analyze_workflow
from .version_migrator import migrate_workflow_schema
from .ir_generator import generate_ir

logger = logging.getLogger(__name__)

async def compile_workflow(json_str: str) -> dict:
    """Full compilation pipeline from JSON to IR"""
    try:
        # 1. Load and preprocess
        logger.info("Loading workflow")
        json_dict = load_raw_json(json_str)
        workflow_dict, raw_nodes = preprocess_n8n_json(json_dict)
        
        # 2. Version migration
        logger.info("Migrating workflow schema")
        workflow_dict = migrate_workflow_schema(workflow_dict)
        
        # 3. Validation
        logger.info("Validating workflow structure")
        raw_workflow = validate_structure(workflow_dict)
        
        # 4. Normalization
        logger.info("Building AST")
        ast = parse_to_ast(raw_workflow.dict())
        
        # 5. Connection mapping
        logger.info("Building connections")
        build_connections(ast)
        
        # 6. Metadata enrichment
        logger.info("Enriching metadata")
        enrich_metadata(ast.nodes, raw_nodes)
        
        # 7. Node interpretation (LLM)
        logger.info("Interpreting nodes with LLM")
        safe_nodes = [build_safe_node(node) for node in ast.nodes.values()]
        
        # Interpret nodes with error handling
        results = []
        for node in safe_nodes:
            try:
                result = await interpret_node(node)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to interpret node {node['id']}: {str(e)}")
                # Use original config as fallback
                results.append({"resolved_config": ast.nodes[node['id']].config})
        
        # Apply resolved configs
        for (node_id, node), result in zip(ast.nodes.items(), results):
            node.resolved_config = result["resolved_config"]
        
        # 8. Static analysis
        logger.info("Running static analysis")
        dead_nodes, cycles = analyze_workflow(ast)
        
        # 9. Generate IR
        logger.info("Generating IR")
        ir = generate_ir(ast)
        
        # Add analysis results to IR
        ir_dict = ir.dict()
        ir_dict["analysis"] = {
            "dead_nodes": dead_nodes,
            "cycles": cycles
        }
        
        logger.info("Compilation successful")
        return ir_dict
        
    except Exception as e:
        logger.exception("Workflow compilation failed")
        raise RuntimeError("Workflow compilation failed") from e
