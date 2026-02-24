# 🚀 AWS EC2 Production Deployment Guide
## Dilshaj Infotech AI Chatbot — FastAPI + LangGraph + Ollama

---

## 📋 Recommended EC2 Instance

| Tier | Instance | vCPU | RAM | Storage | Cost (~) | Notes |
|---|---|---|---|---|---|---|
| **Minimum** | `t3.large` | 2 | 8 GB | 30 GB | ~$60/mo | Slow LLM responses |
| **Recommended** | `t3.xlarge` | 4 | 16 GB | 50 GB | ~$120/mo | Good performance |
| **Best** | `c5.2xlarge` | 8 | 16 GB | 50 GB | ~$250/mo | Fastest CPU inference |
| **GPU (fast)** | `g4dn.xlarge` | 4 | 16 GB | 50 GB + T4 GPU | ~$380/mo | Real-time responses |

> **OS:** Ubuntu 22.04 LTS (recommended)  
> **Root volume:** 50 GB gp3 SSD minimum (llama3.1 alone = 4.9 GB)

---

## 🔐 Step 1 — Launch EC2 Instance

```bash
# In AWS Console:
# 1. EC2 → Launch Instance
# 2. AMI: Ubuntu 22.04 LTS
# 3. Instance type: t3.xlarge (recommended)
# 4. Key pair: create/select your .pem key
# 5. Security group — open these ports:
```

### Security Group Rules

| Port | Protocol | Source | Purpose |
|---|---|---|---|
| 22 | TCP | Your IP only | SSH access |
| 80 | TCP | 0.0.0.0/0 | HTTP (redirects to HTTPS) |
| 443 | TCP | 0.0.0.0/0 | HTTPS (Nginx) |
| 8000 | TCP | Your IP only | Direct FastAPI (debug only) |

---

## 💻 Step 2 — Connect & Deploy (One Command!)

```bash
# 1. SSH into your EC2 instance
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

# 2. Clone your repo
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git /opt/dilshaj-chatbot
cd /opt/dilshaj-chatbot

# 3. Edit deploy.sh — set your domain and repo URL
nano deploy.sh
#  REPO_URL="https://github.com/YOUR_USERNAME/YOUR_REPO.git"
#  DOMAIN="your-domain.com"   ← or use EC2 public IP

# 4. Run the deploy script (everything automated!)
chmod +x deploy.sh
./deploy.sh
```

> ⏱️ **First deploy takes 20-30 minutes** (downloads llama3.1 = 4.9GB)  
> ✅ **Subsequent deploys take ~2 minutes** (models cached in Docker volume)

---

## 🌐 Step 3 — Point Domain to EC2 (Optional)

If using a real domain (recommended for SSL):

```bash
# In your DNS provider (e.g., Namecheap, GoDaddy, Route 53):
# Add A record:   your-domain.com   →   YOUR_EC2_PUBLIC_IP
# Add A record: www.your-domain.com →   YOUR_EC2_PUBLIC_IP

# Wait for DNS propagation (5-30 minutes), then:
# In docker/nginx.conf — replace IP with domain name (already done by deploy.sh)
```

---

## 🔒 Step 4 — Real SSL with Let's Encrypt (Production)

Replace self-signed cert with free Let's Encrypt cert:

```bash
# On EC2 — stop Nginx temporarily
docker compose stop nginx

# Install Certbot
sudo apt install certbot -y

# Get certificate (standalone mode)
sudo certbot certonly --standalone \
  -d your-domain.com \
  -d www.your-domain.com \
  --email your@email.com \
  --agree-tos \
  --non-interactive

# Copy certs to docker/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/ssl/
sudo chown $USER:$USER docker/ssl/*.pem

# Restart Nginx with real cert
docker compose start nginx

# Auto-renew certs every 90 days (add to crontab)
echo "0 0 1 * * cd /opt/dilshaj-chatbot && sudo certbot renew --quiet && \
  sudo cp /etc/letsencrypt/live/your-domain.com/*.pem docker/ssl/ && \
  docker compose restart nginx" | sudo crontab -
```

---

## 📊 Step 5 — Monitor & Manage

### Service Status
```bash
cd /opt/dilshaj-chatbot

# See all containers
docker compose ps

# Live logs
docker compose logs -f app          # FastAPI app
docker compose logs -f ollama       # Ollama LLM
docker compose logs -f mongo        # MongoDB
docker compose logs -f nginx        # Nginx access/error

# Resource usage
docker stats                        # CPU/Memory/Network per container
htop                                # EC2 host resources
```

### Health Checks
```bash
# FastAPI health
curl https://your-domain.com/health

# Ollama status + loaded models
curl http://localhost:11434/api/tags

# Prometheus metrics
curl http://localhost:8000/metrics
```

### Common Operations
```bash
# Restart only the app (after code updates)
docker compose restart app

# Full redeploy with latest code
git pull && docker compose build app && docker compose up -d app

# Stop everything
docker compose down

# Stop + wipe all data (⚠️ destructive!)
docker compose down -v

# View FAISS index files
docker compose exec app ls -lh data/faiss_index/

# Access MongoDB shell
docker compose exec mongo mongosh company_app
```

---

## ⚡ Step 6 — Performance Tuning by Instance Type

Edit `.env.production` based on your EC2 instance:

```bash
# t3.large (2 vCPU, 8GB RAM)
OLLAMA_NUM_THREAD=2
MAX_TOKENS=200          # Shorter outputs = faster

# t3.xlarge (4 vCPU, 16GB RAM)
OLLAMA_NUM_THREAD=4
MAX_TOKENS=300

# c5.2xlarge (8 vCPU, 16GB RAM)
OLLAMA_NUM_THREAD=8
MAX_TOKENS=400

# g4dn.xlarge (GPU)  ← Change these settings!
OLLAMA_NUM_GPU=1        # Use GPU!
OLLAMA_NUM_THREAD=4
MAX_TOKENS=500
```

After editing, apply changes:
```bash
docker compose up -d --force-recreate app ollama
```

---

## 🗂️ File Structure After Deployment

```
/opt/dilshaj-chatbot/
├── Dockerfile                  ← Multi-stage build
├── docker-compose.yml          ← Production services
├── docker-compose.override.yml ← Dev overrides (ignored in prod)
├── .env.production             ← Production secrets ⚠️
├── deploy.sh                   ← One-command deploy
├── requirements.txt            ← Pinned Python deps
├── app/                        ← FastAPI application
│   ├── api/v1/chatbot.py
│   ├── core/langgraph/graph.py
│   ├── services/ (llm, rag, memory, payment)
│   └── ...
├── static/                     ← Frontend (HTML/CSS/JS)
├── data/
│   └── company_docs/           ← Your company docs (*.md)
└── docker/
    ├── nginx.conf              ← Nginx reverse proxy config
    ├── mongo-init.js           ← MongoDB seed data
    └── ssl/
        ├── fullchain.pem       ← SSL certificate
        └── privkey.pem         ← SSL private key
```

---

## 🐳 Docker Volumes (Persistent Data)

| Volume | Contents | Size |
|---|---|---|
| `ollama_models` | llama3.1 + nomic-embed-text | ~5.2 GB |
| `mongo_data` | Payment/user records | Small |
| `qdrant_data` | Qdrant standalone (unused) | Small |
| `qdrant_local` | Mem0 long-term memories | Growing |
| `faiss_data` | Company docs FAISS index | Small |

To back up all volumes:
```bash
# Backup
docker run --rm -v dilshaj-chatbot_mongo_data:/data \
  -v $(pwd)/backups:/backup ubuntu \
  tar czf /backup/mongo_backup_$(date +%Y%m%d).tar.gz /data

# Restore
docker run --rm -v dilshaj-chatbot_mongo_data:/data \
  -v $(pwd)/backups:/backup ubuntu \
  tar xzf /backup/mongo_backup_20240224.tar.gz -C /
```

---

## 🔧 Troubleshooting

### App won't start?
```bash
docker compose logs app --tail=50
# Check: Is Ollama healthy? Is .env.production correct?
```

### Ollama model not found?
```bash
# Re-run model puller
docker compose run --rm ollama_puller

# Or manually pull
docker compose exec ollama ollama pull llama3.1
docker compose exec ollama ollama pull nomic-embed-text
```

### Out of memory?
```bash
# Check memory usage
docker stats --no-stream
free -h
# Solution: Upgrade instance or use llama3.2:3b (smaller model)
docker compose exec ollama ollama pull llama3.2:3b
# Then edit .env.production: OLLAMA_MODEL=llama3.2:3b
```

### MongoDB connection error?
```bash
docker compose logs mongo --tail=20
docker compose exec mongo mongosh --eval "db.adminCommand('ping')"
```

---

## 💰 AWS Cost Estimate (Monthly)

| Component | t3.xlarge | g4dn.xlarge (GPU) |
|---|---|---|
| EC2 Instance | ~$120 | ~$380 |
| EBS Storage (50GB) | ~$5 | ~$5 |
| Data transfer (100GB) | ~$9 | ~$9 |
| Elastic IP | Free | Free |
| **Total** | **~$134/mo** | **~$394/mo** |

> 💡 **Tip:** Use Reserved Instances (1-year) for 30-40% savings

---

*Generated for Dilshaj Infotech AI Chatbot — Feb 2026*
