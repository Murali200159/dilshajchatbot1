# 🤖 Dilshaj Infotech AI Chatbot — Production Stack
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-2D3748?style=for-the-badge&logo=langchain)
![Ollama](https://img.shields.io/badge/Ollama-black?style=for-the-badge&logo=ollama)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb)
![Qdrant](https://img.shields.io/badge/Qdrant-darkred?style=for-the-badge&logo=qdrant)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)
A production-ready, high-performance AI chatbot orchestrator built with **FastAPI**, **LangGraph**, and **Ollama**. This system features proactive Retrieval-Augmented Generation (RAG), long-term user memory, and full GPU acceleration support for sub-second responses on AWS EC2.
---
## 🏛️ System Architecture
The system follows a multi-layered agentic architecture designed for low-latency streaming and deep context retention.
*   **API Layer**: FastAPI handles authenticated SSE streaming and rate limiting.
*   **Agentic Orchestration**: LangGraph manages the stateful conversation flow.
*   **Intelligence**: Ollama (llama3.1) serving LLM and Embeddings locally.
*   **Knowledge (RAG)**: FAISS indexes local company docs ([.md](cci:7://file:///c:/Users/sarip/Downloads/fastapi-langgraph-agent-production-ready-template-master/fastapi-langgraph-agent-production-ready-template-master/README.md:0:0-0:0)) for instant retrieval.
*   **Long-Term Memory**: Qdrant stores cross-session user facts and preferences.
*   **User Data**: MongoDB handles session history and user profiles.
> **View the visual architecture**: Once running, visit `http://<your-ip>:8000/static/architecture.html`
---
## ✨ Key Features
-   🚀 **Ultrafast Streaming**: Real-time token streaming via Server-Sent Events (SSE).
-   ⚡ **GPU Acceleration**: Built-in NVIDIA CUDA support for llama3.1 inference on AWS G4dn/G5 instances.
-   🧠 **Stateful Memory**: Remembers user preferences over time using Berlekamp-Massey memory patterns via Qdrant.
-   📄 **Proactive RAG**: Automatically fetches relevant company documentation before the LLM speaks.
-   🔒 **Production Hardened**: Nginx reverse proxy, JWT security, and Docker health-monitoring.
-   📊 **Health Metrics**: Integrated Prometheus-style metrics and health dashboard at `/health`.
---
## 🚀 One-Command Deployment (Production)
This project is optimized for **AWS EC2 (g4dn.xlarge)** or similar GPU instances.
### 1. Prerequisites
- Docker & Docker Compose V2
- NVIDIA Container Toolkit (for GPU support)
### 2. Setup Environment
```bash
cp .env.example .env.production
# Edit .env.production and set your JWT_SECRET_KEY (min 32 chars)
3. Launch
bash
docker compose up -d --build
4. Verify Startup
bash
# Watch the models download (llama3.1 & nomic-embed-text)
docker logs -f dilshaj_ollama_puller
Wait until the logs say "All models ready!"

🛠️ Tech Stack & Services
Service	Technology	Port (Internal)	Port (Public)
Backend	FastAPI / Python 3.11	8000	via Nginx (80)
LLM	Ollama (llama3.1)	11434	Secured (Internal Only)
Vector DB	Qdrant	6333	Secured (Internal Only)
Database	MongoDB 7.0	27017	Secured (Internal Only)
Proxy	Nginx	-	80 / 443
💻 Local Development
If you want to run without Docker:

bash
# Install dependencies
pip install -r requirements.txt
# Start Ollama locally
ollama serve
# Run the app
uvicorn app.main:app --reload
📁 Directory Structure
text
├── app/               # Core application logic
│   ├── api/           # API Endpoints (v1)
│   ├── core/          # Config, Logging, Security
│   ├── services/      # RAG, LLM, Memory, DB
│   └── main.py        # Entry point
├── data/              # Persistent volumes & Docs
├── docker/            # Nginx & Mongo configs
├── static/            # UI & Architecture Dashboard
└── docker-compose.yml # Production orchestration
📝 License
© 2024 Dilshaj Infotech. All rights reserved.
