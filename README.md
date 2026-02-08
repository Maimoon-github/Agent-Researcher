# Agent Researcher

Autonomous research agent system with 15 specialized processing nodes for gathering, analyzing, and generating research documents.

## Features

- **Autonomous Operation**: Continuous research with minimal human intervention
- **Local LLM Processing**: Uses Ollama (Mistral/Qwen) for completely local operation
- **Automatic Model Fallback**: Seamlessly switches models on token limits
- **Quality Validation**: LLM-based and rule-based quality checks
- **Multi-Format Output**: Markdown, PDF, DOCX, HTML export
- **Vector Knowledge Base**: ChromaDB for semantic search and retrieval
- **Comprehensive Monitoring**: Prometheus metrics and structured logging

## Requirements

- Python 3.11+
- Ollama with at least one model installed
- ~8GB RAM recommended

## Quick Start

### 1. Install Dependencies

```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -e .
```

### 2. Start Ollama

```bash
# Install a model
ollama pull mistral:7b-instruct
ollama pull nomic-embed-text

# Start Ollama server
ollama serve
```

### 3. Run the Agent

```bash
# Single query
python -m src.main --query "Latest developments in AI research"

# Interactive mode
python -m src.main --interactive

# Continuous mode
python -m src.main --continuous --interval 30
```

## Configuration

Edit `config/settings.yaml` to customize:

- LLM models and fallback order
- Quality thresholds
- Output formats and paths
- Scraping settings
- Monitoring options

## Architecture

```
Process Orchestrator (Root Node)
├── Data Collection Pipeline
│   ├── Source Discovery Agent
│   ├── Web Scraper Engine
│   ├── Local File Loader
│   └── Data Validator
├── Knowledge Processing Pipeline
│   ├── Data Cleaning Node
│   ├── LLM Analysis Node
│   └── Semantic Indexing Node
├── Document Generation Pipeline
│   ├── Content Assembly Agent
│   ├── Template Engine
│   ├── Formatting Node
│   └── Quality Review Agent
├── Feedback Loop
│   ├── Metrics Collector
│   ├── Improvement Analyzer
│   └── Knowledge Base Updater
└── Monitoring Layer
    └── Logging Node
```

## Usage Examples

### Single Research Query

```python
from src.core.orchestrator import ProcessOrchestrator

orchestrator = ProcessOrchestrator()
result = orchestrator.run(
    query="What are the latest advances in quantum computing?",
    output_format="pdf"
)
print(f"Document: {result['output_path']}")
```

### Continuous Research Loop

```python
from src.main import run_continuous_loop

run_continuous_loop(interval_minutes=60)
```

## Output

Generated documents are saved to `./output/documents/` by default. Each document includes:

- Title and metadata
- Structured sections
- Citations/references
- Quality score

## Monitoring

- **Logs**: `./logs/agent_researcher.log`
- **Session logs**: `./logs/sessions/*.json`
- **Prometheus metrics**: `http://localhost:9090/metrics`

## License

MIT
