# main.py
import asyncio
import json
import logging
import argparse
import sys
from .pipeline import compile_workflow


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

def load_workflow_json(file_path: str) -> str:
    """Load workflow JSON from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.error(f"Workflow file not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading workflow file: {str(e)}")
        sys.exit(1)

async def main():
    parser = argparse.ArgumentParser(description='Compile n8n workflow to IR')
    parser.add_argument('workflow_file', type=str, 
                        help='Path to n8n workflow JSON file')
    parser.add_argument('--output', type=str, default='ir_output.json',
                        help='Output file for IR (default: ir_output.json)')
    
    args = parser.parse_args()
    
    try:
        # Load workflow JSON from file
        json_str = load_workflow_json(args.workflow_file)
        
        # Compile workflow
        ir = await compile_workflow(json_str)
        
        # Save output
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(ir, f, indent=2)
            
        print(f"IR Generation Successful! Output saved to {args.output}")
        print(f"Workflow name: {ir.get('name', 'Unnamed Workflow')}")
        print(f"Nodes count: {len(ir.get('nodes', {}))}")
        print(f"Edges count: {len(ir.get('edges', []))}")
        
        # Print analysis results if available
        if 'analysis' in ir:
            print("\nStatic Analysis Results:")
            if ir['analysis'].get('dead_nodes'):
                print(f"⚠️ Dead nodes: {ir['analysis']['dead_nodes']}")
            else:
                print("✅ No dead nodes found")
                
            if ir['analysis'].get('cycles'):
                print(f"⚠️ Cycles detected: {ir['analysis']['cycles']}")
            else:
                print("✅ No cycles found")
                
    except Exception as e:
        logging.exception("Workflow compilation failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
