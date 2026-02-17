# Tech Stack and Architecture

Our system is designed for high performance and scalability.

1. **Framework**: FastAPI for the web API, providing high concurrency and asynchronous support.
2. **AI Engine**: LangGraph for building complex agentic workflows and stateful applications.
3. **Database**: MongoDB (via Motor) for core application data and user sessions.
4. **Vector DB**: FAISS for efficient local similarity search (RAG).
5. **LLM**: OpenAI GPT models for natural language processing and agentic reasoning.
6. **Observability**: Structured logging with `structlog`, metrics with Prometheus, and tracing with Langfuse.

Design decisions prioritize modularity and ease of extension.
