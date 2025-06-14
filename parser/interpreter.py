# parser/interpreter.py
import json
import hashlib
import asyncio
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from groq import AsyncGroq
from .cache import get as get_cache, set as set_cache

logger = logging.getLogger(__name__)

# Initialize Groq client
llm = AsyncGroq(
    api_key="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",
)

class LLMInterpretationError(Exception):
    """Custom exception for LLM interpretation failures"""

def build_safe_node(ast_node) -> dict:
    """Create LLM-safe node representation without sensitive data"""
    safe_credentials = {}
    if ast_node.credentials:
        for cred_type, cred_info in ast_node.credentials.items():
            safe_credentials[cred_type] = {
                "name": cred_info.get("name"),
                "type": cred_type
            }
    
    return {
        "id": ast_node.id,
        "name": ast_node.name,
        "type": ast_node.type,
        "type_version": ast_node.type_version,
        "config": ast_node.config,
        "credentials": safe_credentials,
        "metadata": {
            "llm_hint": ast_node.metadata.llm_hint if ast_node.metadata else None
        }
    }

def build_prompt(safe_node: dict) -> str:
    return f"""
You are an expert automation engineer converting workflow nodes to executable configurations.
Given this node specification, return ONLY the resolved configuration in JSON format.

Required response format:
{{
  "resolved_config": {{
    // Resolved configuration object
  }}
}}

Important rules:
1. Respond with exactly one JSON object that matches the required format
2. Do not include any explanations, markdown, or extra text
3. Ensure all JSON strings are properly escaped
4. If a value looks like a template expression (starts with '={{'), preserve it exactly
5. For empty values, use null or empty strings as appropriate
6. Maintain all keys from the original config
7. Only modify values that need resolution

Node specification:
{json.dumps(safe_node, indent=2)}
""".strip()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(LLMInterpretationError),
)
async def interpret_node(safe_node: dict) -> dict:
    """Resolve node configuration using LLM with retries"""
    node_id = safe_node["id"]
    
    # Generate cache key
    cache_key = hashlib.sha256(
        json.dumps(safe_node, sort_keys=True).encode()
    ).hexdigest()
    
    # Check cache
    if cached := get_cache(cache_key):
        logger.debug(f"Using cached config for {node_id}")
        return cached
        
    # Call LLM
    prompt = build_prompt(safe_node)
    logger.info(f"Interpreting node {node_id} with LLM")
    
    try:
        response = await llm.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192",
            temperature=0.1,
            response_format={"type": "json_object"},
            timeout=30
        )
        
        content = response.choices[0].message.content
        
        # Validate response structure
        try:
            result = json.loads(content)
            if "resolved_config" not in result:
                raise LLMInterpretationError("Response missing 'resolved_config' key")
                
            # Cache successful result
            set_cache(cache_key, result)
            return result
        except json.JSONDecodeError as e:
            raise LLMInterpretationError(f"Invalid JSON response: {content}") from e
            
    except Exception as e:
        logger.error(f"LLM interpretation failed for {node_id}: {str(e)}")
        
        # For specific errors, try a more reliable model
        if "400" in str(e) or "json" in str(e).lower():
            logger.info(f"Retrying with reliable model for {node_id}")
            try:
                response = await llm.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-8b-8192",  # More reliable for JSON
                    temperature=0.0,
                    response_format={"type": "json_object"},
                    timeout=45
                )
                content = response.choices[0].message.content
                result = json.loads(content)
                
                # Validate fallback response
                if "resolved_config" not in result:
                    raise LLMInterpretationError("Fallback response missing 'resolved_config' key")
                
                # Cache successful fallback
                set_cache(cache_key, result)
                return result
            except Exception as fallback_e:
                logger.error(f"Fallback model failed for {node_id}: {str(fallback_e)}")
                raise LLMInterpretationError("Both model attempts failed") from fallback_e
                
        raise LLMInterpretationError(f"LLM API error: {str(e)}") from e
