# parser/static_analyzer.py
from .models import WorkflowAST
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

def detect_dead_nodes(ast: WorkflowAST) -> List[str]:
    """Find unreachable nodes"""
    # Find roots (nodes with no inputs)
    roots = [n for n in ast.nodes.values() if not n.inputs]
    
    # DFS to find all reachable nodes
    reachable = set()
    
    def dfs(node):
        if node.id in reachable:
            return
        reachable.add(node.id)
        for conn in node.connections:
            dfs(conn)
    
    for root in roots:
        dfs(root)
    
    # Find dead nodes
    return [nid for nid in ast.nodes if nid not in reachable]

def detect_cycles(ast: WorkflowAST) -> List[List[str]]:
    """Detect cycles using iterative DFS"""
    cycles = []
    visited = set()
    stack = []
    path_map = {}
    
    for node in ast.nodes.values():
        if node.id in visited:
            continue
            
        stack.append(node)
        path_map[node.id] = [node.id]
        
        while stack:
            current = stack.pop()
            current_path = path_map[current.id]
            
            for neighbor in current.connections:
                if neighbor.id in current_path:
                    # Cycle detected
                    cycle_start = current_path.index(neighbor.id)
                    cycles.append(current_path[cycle_start:] + [neighbor.id])
                    continue
                    
                if neighbor.id not in visited:
                    visited.add(neighbor.id)
                    new_path = current_path + [neighbor.id]
                    path_map[neighbor.id] = new_path
                    stack.append(neighbor)
                    
    return cycles

def analyze_workflow(ast: WorkflowAST) -> Tuple[List[str], List[List[str]]]:
    dead_nodes = detect_dead_nodes(ast)
    cycles = detect_cycles(ast)
    
    if dead_nodes:
        logger.warning(f"Dead nodes detected: {dead_nodes}")
    if cycles:
        logger.warning(f"Cycles detected: {cycles}")
    
    return dead_nodes, cycles
