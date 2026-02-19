``````

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
