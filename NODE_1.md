You are an expert AI architect specializing in building multi-agent systems with LangChain, LangGraph, CrewAI, and Pydantic. Your task is to design a highly optimized, production-ready **Source Discovery Agent** node. This agent will be part of a larger research automation pipeline.

---

### **1. Objective**
Design and implement a **Source Discovery Agent** that autonomously identifies and validates information sources based on a given research topic and credibility requirements. The agent must:
- Accept a research topic (string) and credibility requirements (structured criteria).
- Discover relevant sources (web pages, documents, APIs) using web search or pre-defined seed lists.
- Validate each source against credibility requirements (e.g., domain authority, recency, content relevance).
- Output a curated list of sources with rich metadata.
- Respect `robots.txt` and ethical scraping practices.

The agent will be integrated with:
- **Upstream**: Process Orchestrator (provides input topic and credibility rules).
- **Downstream**: Web Scraper Engine and Local File Loader (consume the curated source list).

---

### **2. Constraints & Requirements**
- **Open-Source & Free**: All libraries and tools must be open-source and freely usable.  
  - **Mandatory tools**: `BeautifulSoup4`, `Requests`, `robotstxt_parser` (or `reppy`/`urllib.robotparser`).
  - **Frameworks**: LangChain, LangGraph (or CrewAI), Pydantic, LangSmith (optional for tracing).
- **Structure**: The agent must be implemented as a **LangGraph node** or a **CrewAI agent/task** with clear input/output schemas defined via Pydantic.
- **Output Format**: The curated source list must be a list of Pydantic models containing at least:
  - `url: str`
  - `title: Optional[str]`
  - `description: Optional[str]`
  - `domain_authority_score: float` (or credibility score)
  - `last_updated: Optional[datetime]`
  - `content_type: str` (e.g., "webpage", "pdf", "news")
  - `relevance_score: float` (how well it matches the topic)
  - `validation_status: bool` (passed credibility checks)
- **Credibility Requirements**: Should be a flexible Pydantic model that can include fields like:
  - `min_domain_authority: float` (0-1)
  - `max_age_days: int` (filter sources older than this)
  - `required_content_types: List[str]`
  - `trusted_domains: List[str]` (whitelist)
- **Error Handling**: Gracefully handle network errors, invalid URLs, and robots.txt disallowances. Log failures via LangSmith if used.

---

### **3. Expected Output**
You must provide a **complete implementation blueprint** including:
- **Pydantic Models**: For input (topic + credibility requirements) and output (curated source list with metadata).
- **Agent Implementation**:
  - If using **LangGraph**: Define the node function, state schema, and how it integrates into a graph.
  - If using **CrewAI**: Define the agent, its tools, and the task it performs.
- **Tooling**: Detailed usage of `requests`, `BeautifulSoup`, and `robotstxt_parser` to fetch and parse sources, extract metadata, and check robots.txt.
- **Discovery Mechanism**:
  - Use a search API (e.g., SerpAPI, but must be free; alternatively use `googlesearch-python` library which is free but unofficial) OR
  - Implement a simple crawler starting from seed URLs (e.g., Wikipedia, academic sources) – specify which approach.
  - Note: If using a search API, ensure it has a free tier; otherwise, default to a fallback method.
- **Credibility Validation**:
  - Compute domain authority using a heuristic (e.g., Moz DA via free API? Not feasible; suggest using `tld` and a precomputed domain list or a simple heuristic like presence of certain TLDs, HTTPS, etc.). For this exercise, propose a simplified but extensible approach.
  - Check recency by parsing `last-modified` headers or meta tags.
  - Relevance: extract keywords from the page title/description and compare with research topic using basic NLP (e.g., TF-IDF via `sklearn` or simple keyword matching). Note that full NLP may be heavy; suggest lightweight alternatives.
- **Integration Guidance**:
  - How the agent receives input from the orchestrator (e.g., via shared state in LangGraph or via task inputs in CrewAI).
  - How the output is passed downstream to the Web Scraper Engine and Local File Loader.
- **Testing & Validation**: Provide example usage with a sample research topic and credibility requirements, showing the expected output format.

---

### **4. Implementation Instructions (Step-by-Step)**
1. **Setup Environment**:
   - List required Python packages (`pip install` commands).
   - Configure LangSmith (optional) for tracing.

2. **Define Pydantic Models**:
   - `CredibilityRequirements`
   - `SourceMetadata` (output model)
   - `SourceDiscoveryInput` (contains topic and requirements)

3. **Build Discovery Tools**:
   - Implement a function `search_web(topic: str, num_results: int = 10) -> List[str]` using a free search library (e.g., `googlesearch-python`). Handle rate limiting.
   - Alternatively, implement `fetch_seed_urls(topic: str) -> List[str]` from curated directories.

4. **Implement Robots.txt Check**:
   - Use `urllib.robotparser` to check if fetching a URL is allowed.

5. **Fetch and Parse**:
   - Use `requests` with a polite User-Agent to fetch each URL.
   - Parse with `BeautifulSoup` to extract title, description, and last-updated meta tags.

6. **Credibility Scoring**:
   - Domain authority: implement a simple function based on TLD, HTTPS, or a static list.
   - Recency: parse headers or meta, compare with current date.
   - Relevance: compute cosine similarity between topic and page text (optional; if too heavy, fallback to keyword matching).

7. **Assemble Agent Logic**:
   - Combine steps into a single function/class that takes input and returns list of `SourceMetadata`.

8. **Integrate with Framework**:
   - For LangGraph: define state and node; for CrewAI: define agent and task.

9. **Error Handling & Logging**:
   - Use try-except blocks; log errors to LangSmith if available.

10. **Example**:
    - Provide a runnable example with `topic = "AI ethics"` and credibility requirements: `min_domain_authority=0.7`, `max_age_days=365`.

---

### **5. Architectural Guidance**
- **Upstream Communication**: The Process Orchestrator should pass a `SourceDiscoveryInput` object to this agent. In LangGraph, this is part of the shared state; in CrewAI, it's the task input.
- **Downstream Communication**: The agent's output (list of `SourceMetadata`) should be stored in the shared state or returned as a task output for the next agents (Web Scraper Engine, Local File Loader). These agents will consume the URLs and metadata.
- **Scalability**: The agent may need to handle many topics concurrently. Suggest using async requests or thread pools (with care for rate limits).
- **Ethics & Compliance**: Always respect `robots.txt` and include a delay between requests. The agent should not overload servers.
- **Extensibility**: Design the credibility module to be easily swappable (e.g., plug in a more sophisticated authority scorer later).

---

### **6. Final Deliverable**
Provide a comprehensive response that includes:
- **Code blocks** for all Pydantic models, tool functions, and the agent node.
- **Explanation** of key design decisions and trade-offs.
- **Instructions** on how to integrate this agent into a larger LangGraph or CrewAI application.
- **Example output** for a sample run.

Ensure the solution is **implementation-ready**—a developer should be able to copy the code, install dependencies, and run the agent with minimal changes.

Now, generate the response.