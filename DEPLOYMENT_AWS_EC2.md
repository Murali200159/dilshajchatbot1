# Deploying to AWS EC2 (Ubuntu) with Ollama

## 1. Instance Setup
- **Launch Instance**: Ubuntu Server 22.04 LTS (t3.xlarge or higher recommended for LLaMA 3/8B).
- **Security Group**:
  - Allow TCP 22 (SSH)
  - Allow TCP 8000 (FastAPI)
  - Allow TCP 11434 (Ollama API - restrict to VPC/Localhost if possible)

## 2. Install Docker & Ollama
SSH into your instance:
```bash
# Update and install Docker
sudo apt-get update
sudo apt-get install -y docker.io
sudo usermod -aG docker $USER
newgrp docker

# Install Ollama (Native Linux)
curl -fsSL https://ollama.com/install.sh | sh
```

## 3. Setup Fine-Tuned Model (dilshaj-ai)
If you have a GGUF file (e.g., `dilshaj-llama3.gguf`), upload it via SCP:
```bash
scp -i your-key.pem ./dilshaj-llama3.gguf ubuntu@your-ec2-ip:~/
```

On EC2, create a Modelfile:
```bash
echo "FROM ./dilshaj-llama3.gguf" > Modelfile
```

Create the custom model in Ollama:
```bash
ollama create dilshaj-ai -f Modelfile
```
*Verify it works:* `ollama run dilshaj-ai "Hello"`

## 4. Run the Application
Clone your repo:
```bash
git clone https://github.com/your-repo/fastapi-langgraph-agent.git
cd fastapi-langgraph-agent
```

Create `.env`:
```bash
cp .env.example .env
nano .env
# Set OLLAMA_BASE_URL=http://host.docker.internal:11434 (if running app in Docker)
# OR OLLAMA_BASE_URL=http://localhost:11434 (if running app natively)
```

Run with Docker Compose:
```bash
docker compose up -d --build
```

**Note**: Since Ollama is running on the host (not in Docker), you might need to adjust `OLLAMA_BASE_URL` or run Ollama inside Docker too. To access host Ollama from container, use `http://172.17.0.1:11434` or `http://host.docker.internal:11434`.

## 5. Verify
- **API**: `http://your-ec2-ip:8000/docs`
- **Frontend**: `http://your-ec2-ip:8000/` (Static)
