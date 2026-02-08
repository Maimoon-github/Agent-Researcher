"""
State Management for Agent Researcher

Defines the state schema and data structures used throughout the workflow.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


class NodeStatus(str, Enum):
    """Status of a node execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"


class SourceType(str, Enum):
    """Type of data source."""
    WEB = "web"
    LOCAL_FILE = "local_file"
    DATABASE = "database"
    API = "api"


class DocumentFormat(str, Enum):
    """Output document format."""
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"


class Source(BaseModel):
    """Represents a data source."""
    url: Optional[str] = None
    path: Optional[str] = None
    source_type: SourceType
    credibility_score: float = 0.5
    metadata: Dict[str, Any] = Field(default_factory=dict)
    last_accessed: Optional[datetime] = None
    robots_allowed: bool = True


class RawData(BaseModel):
    """Raw data extracted from a source."""
    source_id: str
    content: str
    content_type: str = "text/plain"
    extracted_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CleanedChunk(BaseModel):
    """Cleaned and processed text chunk."""
    chunk_id: str
    source_id: str
    content: str
    tokens: int = 0
    entities: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    embedding: Optional[List[float]] = None


class KnowledgeItem(BaseModel):
    """A piece of structured knowledge."""
    item_id: str
    content: str
    source_ids: List[str] = Field(default_factory=list)
    confidence: float = 0.5
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None


class DocumentDraft(BaseModel):
    """Draft document being assembled."""
    title: str
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    revision_count: int = 0


class QualityReview(BaseModel):
    """Quality review results."""
    approved: bool = False
    score: float = 0.0
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    reviewed_at: datetime = Field(default_factory=datetime.now)


class NodeResult(BaseModel):
    """Result from a node execution."""
    node_name: str
    status: NodeStatus
    data: Any = None
    error: Optional[str] = None
    duration_ms: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)
    retry_count: int = 0


class Metrics(BaseModel):
    """Performance metrics."""
    documents_generated: int = 0
    sources_processed: int = 0
    llm_calls: int = 0
    total_tokens_used: int = 0
    average_quality_score: float = 0.0
    errors_count: int = 0
    node_timings: Dict[str, List[int]] = Field(default_factory=dict)


class AgentState(TypedDict, total=False):
    """
    Main state object passed through the LangGraph workflow.
    
    This TypedDict defines the complete state schema for the agent system.
    All nodes read from and write to this shared state.
    """
    # Session info
    session_id: str
    query: str
    started_at: str
    
    # Current execution context
    current_node: str
    current_model: str
    model_switch_count: int
    
    # Data Collection Pipeline
    sources: List[Dict[str, Any]]
    raw_data: List[Dict[str, Any]]
    validated_data: List[Dict[str, Any]]
    
    # Knowledge Processing Pipeline
    cleaned_chunks: List[Dict[str, Any]]
    extracted_knowledge: List[Dict[str, Any]]
    indexed_count: int
    
    # Document Generation Pipeline
    document_draft: Dict[str, Any]
    formatted_document: Dict[str, Any]
    output_path: str
    output_format: str
    
    # Quality Review
    quality_review: Dict[str, Any]
    revision_count: int
    approved: bool
    
    # Feedback Loop
    metrics: Dict[str, Any]
    improvements: List[str]
    
    # Execution Tracking
    node_results: List[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]
    
    # Control flags
    should_continue: bool
    pipeline_complete: bool


def create_initial_state(query: str, session_id: Optional[str] = None) -> AgentState:
    """Create initial state for a new research session."""
    import uuid
    
    return AgentState(
        session_id=session_id or str(uuid.uuid4()),
        query=query,
        started_at=datetime.now().isoformat(),
        current_node="orchestrator",
        current_model="",
        model_switch_count=0,
        sources=[],
        raw_data=[],
        validated_data=[],
        cleaned_chunks=[],
        extracted_knowledge=[],
        indexed_count=0,
        document_draft={},
        formatted_document={},
        output_path="",
        output_format="markdown",
        quality_review={},
        revision_count=0,
        approved=False,
        metrics={
            "documents_generated": 0,
            "sources_processed": 0,
            "llm_calls": 0,
            "total_tokens_used": 0,
            "errors_count": 0,
        },
        improvements=[],
        node_results=[],
        errors=[],
        warnings=[],
        should_continue=True,
        pipeline_complete=False,
    )
