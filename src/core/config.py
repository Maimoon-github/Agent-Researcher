"""
Configuration Manager for Agent Researcher

Loads and validates YAML configuration with environment overrides.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field
from loguru import logger


class LLMTokenLimits(BaseModel):
    """Token limit configuration for model switching."""
    input_warning: int = 6000
    input_max: int = 8000
    output_max: int = 4096


class LLMConfig(BaseModel):
    """LLM configuration with fallback support."""
    primary_model: str = "mistral:7b-instruct"
    fallback_models: List[str] = Field(default_factory=lambda: ["qwen2:7b", "llama3.1:8b"])
    ollama_base_url: str = "http://localhost:11434"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120
    token_limits: LLMTokenLimits = Field(default_factory=LLMTokenLimits)


class EmbeddingsConfig(BaseModel):
    """Embedding model configuration."""
    model: str = "nomic-embed-text"
    dimensions: int = 768


class ScrapingConfig(BaseModel):
    """Web scraping configuration."""
    max_concurrent: int = 3
    rate_limit_delay: float = 2.0
    timeout: int = 30
    max_retries: int = 3
    respect_robots_txt: bool = True
    user_agent: str = "AgentResearcher/0.1 (Research Bot)"


class VectorDBConfig(BaseModel):
    """Vector database configuration."""
    type: str = "chromadb"
    persist_directory: str = "./data/chroma"
    collection_name: str = "research_knowledge"


class MetadataDBConfig(BaseModel):
    """Metadata database configuration."""
    type: str = "sqlite"
    path: str = "./data/metadata.db"


class StorageConfig(BaseModel):
    """Storage configuration."""
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)
    metadata_db: MetadataDBConfig = Field(default_factory=MetadataDBConfig)


class DocumentsConfig(BaseModel):
    """Document generation configuration."""
    default_format: str = "markdown"
    supported_formats: List[str] = Field(default_factory=lambda: ["markdown", "pdf", "docx"])
    templates_dir: str = "./templates"
    output_dir: str = "./output/documents"


class QualityConfig(BaseModel):
    """Quality threshold configuration."""
    min_confidence_score: float = 0.7
    min_source_credibility: float = 0.6
    max_revision_attempts: int = 3
    fact_check_enabled: bool = True


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    metrics_enabled: bool = True
    prometheus_port: int = 9090
    log_file: str = "./logs/agent_researcher.log"
    log_rotation: str = "10 MB"


class SchedulingConfig(BaseModel):
    """Scheduling configuration."""
    knowledge_refresh_interval: int = 3600
    metrics_collection_interval: int = 60
    cleanup_interval: int = 86400


class ErrorHandlingConfig(BaseModel):
    """Error handling configuration."""
    max_retries: int = 3
    exponential_backoff_base: int = 2
    max_backoff_seconds: int = 60


class SystemConfig(BaseModel):
    """System configuration."""
    name: str = "Agent Researcher"
    version: str = "0.1.0"
    log_level: str = "INFO"
    data_dir: str = "./data"
    output_dir: str = "./output"


class Config(BaseModel):
    """Main configuration container."""
    system: SystemConfig = Field(default_factory=SystemConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    scraping: ScrapingConfig = Field(default_factory=ScrapingConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    documents: DocumentsConfig = Field(default_factory=DocumentsConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    scheduling: SchedulingConfig = Field(default_factory=SchedulingConfig)
    error_handling: ErrorHandlingConfig = Field(default_factory=ErrorHandlingConfig)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """Load configuration from YAML file with environment overrides."""
        if config_path is None:
            # Default config paths to search
            search_paths = [
                Path("config/settings.yaml"),
                Path("settings.yaml"),
                Path.home() / ".agent_researcher" / "settings.yaml",
            ]
            for path in search_paths:
                if path.exists():
                    config_path = str(path)
                    break
        
        config_data: Dict[str, Any] = {}
        
        if config_path and Path(config_path).exists():
            logger.info(f"Loading configuration from {config_path}")
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
        else:
            logger.warning("No configuration file found, using defaults")
        
        # Apply environment variable overrides
        config_data = cls._apply_env_overrides(config_data)
        
        return cls(**config_data)
    
    @staticmethod
    def _apply_env_overrides(config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        env_mappings = {
            "AGENT_OLLAMA_URL": ("llm", "ollama_base_url"),
            "AGENT_LLM_MODEL": ("llm", "primary_model"),
            "AGENT_LOG_LEVEL": ("system", "log_level"),
            "AGENT_DATA_DIR": ("system", "data_dir"),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.environ.get(env_var)
            if value:
                if section not in config_data:
                    config_data[section] = {}
                config_data[section][key] = value
                logger.debug(f"Applied env override: {env_var}")
        
        return config_data
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            Path(self.system.data_dir),
            Path(self.system.output_dir),
            Path(self.storage.vector_db.persist_directory),
            Path(self.documents.templates_dir),
            Path(self.documents.output_dir),
            Path(self.monitoring.log_file).parent,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def reload_config(config_path: Optional[str] = None) -> Config:
    """Reload configuration from file."""
    global _config
    _config = Config.load(config_path)
    return _config
