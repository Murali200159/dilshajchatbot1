# Deploying to AWS EC2 (GPU) with Local LLaMA Fine-Tuned Model

## 1. Instance Setup
- **Instance Type**: g4dn.2xlarge (Tesla T4) or g5.xlarge (A10G).
- **AMI**: Deep Learning AMI (Ubuntu 22.04) recommended, or standard Ubuntu with NVIDIA drivers installed.
- **Security Group**:
  - Allow TCP 22 (SSH)
  - Allow TCP 8000 (FastAPI)

## 2. Environment Setup (Pip)
```bash
# Clone Repo
git clone https://github.com/your-repo/fastapi-langgraph-agent.git
cd fastapi-langgraph-agent

# Install Python 3.10+
sudo apt install python3.10-venv -y
python3 -m venv venv
source venv/bin/activate

# Install Dependencies (including GPU libs)
pip install -r requirements.txt
# Ensure torch is CUDA-enabled (usually handled by requirements, but verify)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## 3. Prepare Fine-Tuned Model
You must have your fine-tuned model (adapter merged with base) in a local folder.
SCPs your model to the server:
```bash
# Example: Uploading 'dilshaj-v1' folder
scp -r ./models/finetuned/dilshaj-v1 ubuntu@your-ec2-ip:~/fastapi-langgraph-agent/models/finetuned/dilshaj-v1
```

## 4. Configuration
Create/Edit `.env`:
```bash
cp .env.example .env
nano .env
```
Ensure these values are set to enable Local Model Loading:
```ini
USE_FINETUNED_MODEL=true
FINETUNED_MODEL_PATH=/home/ubuntu/fastapi-langgraph-agent/models/finetuned/dilshaj-v1
```

## 5. Run Application
Run with Uvicorn (Native):
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```
*Note: Use 1 worker because the model is loaded into VRAM. Multiple workers will OOM.*

## 6. Verification
Check logs to see:
`llm_service_initialized provider=local_transformers model=... device=cuda`

Test API:
`curl http://localhost:8000/health`
