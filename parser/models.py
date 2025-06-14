# parser/models.py
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ASTNode

class RuntimeEnv(BaseModel):
    timeout: Optional[int] = None
    retries: Optional[int] = None
    memory_limit: Optional[str] = None
    env_vars: Dict[str, str] = Field(default_factory=dict)

class NodeMetadata(BaseModel):
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    last_modified: Optional[str] = None
    llm_hint: Optional[str] = None
    original_raw_node: Optional[Dict[str, Any]] = None

class RawNode(BaseModel):
    id: str
    name: Optional[str] = None
    type: str
    type_version: Optional[str] = None
    config: Dict[str, Any] = {}
    next: List[str] = Field(default_factory=list)  # This is the key change
    disabled: bool = False
    credentials: Optional[Dict[str, Any]] = None
    position: Optional[List[int]] = None
    webhook_id: Optional[str] = Field(None, alias="webhookId")
    
    @field_validator('type_version', mode='before')
    def convert_type_version(cls, v):
        """Convert type version to string if it's numeric"""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return str(v)
        return v

class RawWorkflow(BaseModel):
    name: Optional[str] = None
    nodes: Dict[str, RawNode] = Field(default_factory=dict)

class ASTNode(BaseModel):
    id: str
    name: Optional[str] = None
    type: str
    type_version: Optional[str] = None
    config: Dict[str, Any] = {}
    connections: List['ASTNode'] = Field(default_factory=list)
    inputs: List[str] = Field(default_factory=list)
    next: List[str] = Field(default_factory=list)  # Added this field
    resolved_config: Dict[str, Any] = Field(default_factory=dict)
    runtime_env: Optional[RuntimeEnv] = None
    metadata: Optional[NodeMetadata] = None
    credentials: Optional[Dict[str, Any]] = None
    disabled: bool = False
    position: Optional[List[int]] = None
    webhook_id: Optional[str] = None
    
    @field_validator('type_version', mode='before')
    def convert_type_version(cls, v):
        """Convert type version to string if it's numeric"""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return str(v)
        return v

class WorkflowAST(BaseModel):
    name: Optional[str] = None
    nodes: Dict[str, ASTNode] = Field(default_factory=dict)

class IREdge(BaseModel):
    from_node: str
    to_node: str

class IRGraph(BaseModel):
    name: Optional[str] = None
    nodes: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    edges: List[IREdge] = Field(default_factory=list)

# Resolve forward references
ASTNode.model_rebuild()
