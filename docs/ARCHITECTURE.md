# System Architecture

## Overview

The Agent Researcher is an autonomous system designed to conduct research, analyze information, and generate high-quality documents locally.

## Core Components

### 1. Process Orchestrator
The central brain of the system, implemented using **LangGraph**. It manages the state and coordinates the execution of specialized processing nodes.

### 2. Processing Nodes (15 Specialized Agents)

#### Data Collection Pipeline
- **Source Discovery**: Uses LLM to identify relevant URLs and local files.
- **Web Scraper**: robustly extracts content from web pages using `httpx` and `BeautifulSoup`.
- **File Loader**: Reads local documents (PDF, DOCX, etc.).
- **Data Validator**: Ensures data quality and structural integrity.

#### Knowledge Processing Pipeline
- **Data Cleaning**: Normalizes text and removes noise.
- **LLM Analysis**: Extracts entities, summaries, and key facts using local LLM.
- **Semantic Indexing**: Stores knowledge in **ChromaDB** for retrieval.

#### Document Generation Pipeline
- **Content Assembly**: Uses RAG to compose document sections.
- **Template Engine**: Formats content using Jinja2 templates.
- **Formatting**: Exports to final formats (Markdown, PDF, DOCX, HTML).
- **Quality Review**: Evaluates output against quality criteria using LLM.

#### Feedback Loop
- **Metrics Collector**: Aggregates performance data.
- **Improvement Analyzer**: Identifies optimization opportunities.
- **KB Updater**: Refines the knowledge base based on feedback.

#### Monitoring
- **Logging Node**: Centralized structured logging.

### 3. State Management
The system uses a typed `AgentState` dictionary passed between nodes, containing:
- Session metadata
- Raw and processed data
- Extracted knowledge
- Document drafts
- Metrics and logs

### 4. Storage Layer
- **ChromaDB**: Vector store for semantic knowledge.
- **SQLite**: Metadata and session history.
- **File System**: Raw artifacts and final documents.

### 5. LLM Management
A robust `LLMManager` handles:
- Connection to **Ollama**.
- Automatic model fallback (e.g., Mistral -> Qwen).
- Token usage tracking.
- Error handling and retries.

## Data Flow

1. **Input**: User provides a research query.
2. **Discovery**: Agent identifies sources.
3. **Collection**: Content is scraped/loaded.
4. **Processing**: content is cleaned, chunked, and analyzed.
5. **Indexing**: Knowledge is stored in vector DB.
6. **Assembly**: Agent retrieves relevant info and writes draft.
7. **Review**: Draft is reviewed and revised if necessary.
8. **Output**: Final document is exported.

## Monitoring

- **Prometheus**: Exposes metrics on port 9090.
- **Grafana**: Visualizes performance (optional).
- **Logs**: Structured JSON logs for auditing.

## Deployment

The system is containerized using Docker, with services defined in `docker-compose.yml` for easy deployment of the agent and monitoring stack.
