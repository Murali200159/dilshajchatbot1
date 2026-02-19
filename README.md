<<<<<<< HEAD
 #Dilshaj Infotech AI Assistant
=======
# Dilshaj Infotech AI Assistant
>>>>>>> fbfe22fd (Added antigravity modifications and EC2 updates)

A production-ready, single-agent conversational AI system designed to handle company inquiries, user data retrieval, and general chat. Powered by **LLaMA 3 (via Ollama)**, **LangGraph**, **FastAPI**, and **MongoDB**.

## 🚀 Key Features

*   **Single Agent Router Architecture**: Intelligently routes user queries to specific tools or handles them directly via LLM.
*   **Offline Capability**: Entirely self-hosted using **Ollama** and **Local LLMs** (no API keys required!).
*   **Vector Search (RAG)**: Retrieves answers from local company documents (PDF/MD) using FAISS and Ollama Embeddings.
*   **Direct Database Access**: Queries **MongoDB** for real-time user data (e.g., payment status, profiles).
*   **Memory Persistence**: Remembers previous turns in the conversation using MongoDB-backed Checkpointing.
*   **Fine-Tuning Support**: Includes scripts to fine-tune LLaMA on your own custom dataset and load it dynamically.
*   **Production Ready**: Dockerized, async-optimized, and includes comprehensive logging/monitoring hooks.

---

## 🛠️ Technology Stack

*   **Brain**: LLaMA 3 (Default) / Custom Fine-Tuned Models (Adapter Support).
*   **Orchestration**: LangGraph + LangChain.
*   **Backend**: FastAPI (Python 3.10+).
*   **Database**: MongoDB (User Data & Chat History).
*   **Knowledge Base**: FAISS (Local Vector Store).
*   **Frontend**: Static HTML5/JS (Lightweight Web Chat).
*   **Serving**: Uvicorn / Docker.

---

## 📂 Project Structure

```bash
├── app/
│   ├── api/          # FastAPI Routes (/chat/stream, /health)
│   ├── core/         # Config, Logging, LangGraph Definition
│   ├── services/     # LLM (Ollama/Transformers), Database, Memory
│   └── tools/        # RAG Tool, User Data Tool
├── data/
│   └── company_docs/ # Place your Markdown/PDF policies here
├── training/         # LLaMA 3 Fine-Tuning Scripts (LoRA/QLoRA)
├── static/           # Web Chat Interface (HTML/CSS/JS)
├── tests/            # Pytest Suite
└── docker-compose.yml
<<<<<<< HEAD
```

---

## ⚡ Quick Start

### 1. Prerequisites
*   Python 3.10+
*   [Ollama](https://ollama.com/) installed and running (`ollama serve`).
*   MongoDB running locally or in Docker.

### 2. Installation
```bash
# Clone the repo
git clone https://github.com/your-repo/dilshaj-ai-agent.git
cd dilshaj-ai-agent

# Create Virtual Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt
pip install -e .
```

### 3. Configuration
Copy `.env.example` to `.env` and configure:
```ini
# .env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=dilshaj-ai
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=dilshaj_db
```

### 4. Populate Data (Optional)
This script creates dummy users and indexes your `data/company_docs`.
```bash
python scripts/populate_db.py
python scripts/reindex_rag.py
```

### 5. Run the Application
```bash
# Start backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Visit **http://localhost:8000/static/index.html** to chat!

---

## 🎓 Training (Fine-Tuning)

You can fine-tune LLaMA on your own data using the `training/` module.

1.  Place your dataset (JSON) in `training/`.
2.  Run:
    ```bash
    python training/train_lora.py --dataset_path "my_data.json" --new_model_name "my-custom-model"
    ```
3.  Deploy: Set `USE_FINETUNED_MODEL=true` in `.env`.

---

## 🐳 Docker Deployment

To run everything in containers:
```bash
docker-compose up --build
```

---

## ☁️ AWS EC2 Deployment (GPU)

See `DEPLOYMENT_EC2_GPU.md` for detailed instructions on running with NVIDIA GPUs (T4/A10G).

---

## 📝 License
Proprietary / MIT (Edit as needed).

```
fastapi-langgraph-agent-production-ready-template-master/
├── app/                        # 🧠 The Main Application Code
│   ├── api/                    # 🌐 REST API Endpoints (FastAPI)
│   │   └── v1/                 # Version 1 API routes
│   │       ├── api.py          # Main Router (collects all routes)
│   │       └── chatbot.py      # The /chat/stream endpoint (Frontend talks to this!)
│   ├── core/                   # ⚙️ Core Configuration & Logic
│   │   ├── config.py           # Application Settings (reads .env)
│   │   ├── logging.py          # Custom Logger Setup
│   │   ├── langgraph/          # 🤖 The AI Brain (LangGraph)
│   │   │   ├── graph.py        # Defines the Workflow (User -> Tool -> Agent)
│   │   │   └── state.py        # Defines what data the agent remembers per turn
│   │   └── prompts/            # 📝 AI Prompts (System Instructions)
│   │       └── system.md       # The "Persona" of the AI (You are Dilshaj AI...)
│   ├── services/               # 🔌 Integrations with External Services
│   │   ├── llm.py              # Manages Ollama / Local Fine-Tuned Model
│   │   ├── database.py         # Manages MongoDB Connection
│   │   └── memory.py           # Handles Conversation History (Checkpointer)
│   ├── tools/                  # 🛠️ capabilities (The "Hands" of the AI)
│   │   ├── rag/                # Retrieval Augmented Generation (Company Docs)
│   │   └── user_details/       # MongoDB User/Payment Lookup Tool
│   └── main.py                 # 🚀 Entry Point (Starts the FastAPI server)
│
├── data/                       # 🗄️ Local Data Storage
│   └── company_docs/           # 📄 Place your PDFs/MDs here (Policies, Info)
│       ├── refund_policy.md
│       └── ...
│
├── static/                     # 🎨 Frontend (HTML/JS/CSS)
│   ├── index.html              # The Chat Interface
│   ├── style.css
│   └── script.js
│
├── training/                   # 🎓 Fine-Tuning Module
│   ├── train_lora.py           # Script to train custom LLaMA models
│   └── requirements.txt        # Dependencies for training
│
├── tests/                      # 🧪 Automated Tests
│   ├── test_agent_final.py     # Tests the full agent flow
│   └── test_rag_file.py        # Tests document retrieval
│
├── scripts/                    # 📜 Utility Scripts
│   ├── populate_db.py          # Fills MongoDB with dummy user data
│   └── reindex_rag.py          # Rebuilds the FAISS index from 'data/company_docs'
│
├── .env                        # 🔑 Environment Variables (Secrets, Configs)
├── docker-compose.yml          # 🐳 Container Orchestration
├── pyproject.toml              # 📦 Python Dependencies (Poetry style)
├── Makefile                    # ⚡ Shortcuts (make run, make test)
└── DEPLOYMENT_EC2_GPU.md       # 📖 Deployment Guide for AWS
=======
>>>>>>> fbfe22fd (Added antigravity modifications and EC2 updates)
```

---

## ⚡ Quick Start

### 1. Prerequisites
*   Python 3.10+
*   [Ollama](https://ollama.com/) installed and running (`ollama serve`).
*   MongoDB running locally or in Docker.

### 2. Installation
```bash
# Clone the repo
git clone https://github.com/your-repo/dilshaj-ai-agent.git
cd dilshaj-ai-agent

# Create Virtual Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt
pip install -e .
```

### 3. Configuration
Copy `.env.example` to `.env` and configure:
```ini
# .env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=dilshaj-ai
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=dilshaj_db
```

### 4. Populate Data (Optional)
This script creates dummy users and indexes your `data/company_docs`.
```bash
python scripts/populate_db.py
python scripts/reindex_rag.py
```

### 5. Run the Application
```bash
# Start backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Visit **http://localhost:8000/static/index.html** to chat!

---

## 🎓 Training (Fine-Tuning)

You can fine-tune LLaMA on your own data using the `training/` module.

1.  Place your dataset (JSON) in `training/`.
2.  Run:
    ```bash
    python training/train_lora.py --dataset_path "my_data.json" --new_model_name "my-custom-model"
    ```
3.  Deploy: Set `USE_FINETUNED_MODEL=true` in `.env`.

---

## 🐳 Docker Deployment

To run everything in containers:
```bash
docker-compose up --build
```

---

## ☁️ AWS EC2 Deployment (GPU)

See `DEPLOYMENT_EC2_GPU.md` for detailed instructions on running with NVIDIA GPUs (T4/A10G).

---

## 📝 License
Proprietary / MIT (Edit as needed).
