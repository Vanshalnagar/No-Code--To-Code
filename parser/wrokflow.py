# ir_generator.py

from typing import Optional
from models import IRGraph, IREdge, ASTNode
from loader import load_raw_json
from validator import validate_structure
from version_migrator import migrate_workflow_schema
from normalizer import parse_to_ast
from connections import build_connections
from metadata_enricher import enrich_metadata
from static_analyzer import analyze_workflow
from plugin_loader import load_plugins  # assuming exists and supports extensibility
from interpreter import interpret_node


import asyncio


async def generate_ir(json_str: str) -> Optional[IRGraph]:
    """
    Full pipeline: from raw JSON → AST → analyzed & interpreted → IRGraph (for codegen/LLM/export)
    """
    # 1. Load JSON
    try:
        raw_data = load_raw_json(json_str)
    except ValueError as e:
        print(f"🚨 Loader Error: {e}")
        return None

    # 2. Validate
    raw_workflow = validate_structure(raw_data)
    if not raw_workflow:
        print("❌ Stopped at validation step.")
        return None

    # 3. Migrate Schema
    migrated_data = migrate_workflow_schema(raw_data)
    raw_workflow = validate_structure(migrated_data)
    if not raw_workflow:
        print("❌ Stopped at post-migration validation step.")
        return None

    # 4. Normalize to AST
    workflow_ast = parse_to_ast(raw_workflow)

    # 5. Build Connections
    build_connections(raw_workflow, workflow_ast.nodes)

    # 6. Enrich Metadata
    enrich_metadata(workflow_ast.nodes, raw_workflow.nodes)

    # 7. Load Plugins (optional step for extensibility)
    load_plugins(workflow_ast.nodes)

    # 8. Static Analysis
    dead_nodes, cycles = analyze_workflow(workflow_ast)
    if cycles:
        print("🔁 Detected Cycles:")
        for cycle in cycles:
            print("  → ".join(cycle))
    if dead_nodes:
        print("🧟 Dead Nodes:")
        for node_id in dead_nodes:
            print(f"  - {node_id}")

    # 9. Interpret Configs via LLM (async in parallel)
    tasks = [interpret_node(ast.model_dump()) for ast in workflow_ast.nodes.values()]
    interpreted_configs = await asyncio.gather(*tasks)

    for ast_node, resolved in zip(workflow_ast.nodes.values(), interpreted_configs):
        ast_node.resolved_config = resolved.get("resolved_config", {})

    # 10. Generate IRGraph
    ir_nodes = {
        node.id: {
            "id": node.id,
            "name": node.name,
            "type": node.type,
            "resolved_config": node.resolved_config,
            "metadata": node.metadata.model_dump(),
            "runtime_env": node.runtime_env.model_dump() if node.runtime_env else {},
            "credentials": node.credentials or {}
        }
        for node in workflow_ast.nodes.values()
    }

    ir_edges = [
        IREdge(from_node=source.id, to_node=target.id)
        for source in workflow_ast.nodes.values()
        for target in source.connections
    ]

    ir_graph = IRGraph(
        name=workflow_ast.name,
        nodes=ir_nodes,
        edges=ir_edges
    )

    return ir_graph

