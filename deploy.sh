#!/usr/bin/env bash
# =============================================================================
#  Dilshaj Infotech Chatbot — AWS EC2 Production Deploy Script
#  Usage:  chmod +x deploy.sh && ./deploy.sh
#  Tested: Ubuntu 22.04 LTS on t3.xlarge (4 vCPU, 16GB RAM)
# =============================================================================
set -euo pipefail

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*"; exit 1; }
step() { echo -e "\n${BLUE}${BOLD}━━━ $* ━━━${NC}"; }

# ── Config — edit before running ─────────────────────────────────────────────
APP_DIR="/opt/dilshaj-chatbot"
REPO_URL="https://github.com/YOUR_USERNAME/YOUR_REPO.git"   # ← Set your repo
DOMAIN="your-domain.com"                                     # ← Set your domain
EC2_VCPUS=$(nproc)                                           # Auto-detect CPUs

step "1 / 8 — System update"
sudo apt-get update -qq && sudo apt-get upgrade -y -qq
log "System updated"

step "2 / 8 — Install Docker & Docker Compose"
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER"
    log "Docker installed"
else
    log "Docker already installed: $(docker --version)"
fi

if ! command -v docker compose &>/dev/null; then
    sudo apt-get install -y docker-compose-plugin
    log "Docker Compose plugin installed"
else
    log "Docker Compose already installed"
fi

step "3 / 8 — Install helpers (git, curl, htop)"
sudo apt-get install -y -qq git curl htop unzip net-tools
log "Helpers installed"

step "4 / 8 — Clone / update repository"
if [ -d "$APP_DIR/.git" ]; then
    warn "Repo already exists — pulling latest changes"
    cd "$APP_DIR" && git pull origin main
else
    sudo git clone "$REPO_URL" "$APP_DIR"
    sudo chown -R "$USER:$USER" "$APP_DIR"
    log "Repository cloned to $APP_DIR"
fi
cd "$APP_DIR"

step "5 / 8 — Configure production environment"
if [ ! -f ".env.production" ]; then
    cp .env.production .env.production.bak 2>/dev/null || true
    warn ".env.production not found — creating from template"
    cat > .env.production << ENV
APP_ENV=production
ENVIRONMENT=production
PROJECT_NAME="Dilshaj Infotech"
VERSION=1.0.0
DEBUG=false
LOG_LEVEL=info
LOG_FORMAT=json
API_V1_STR=/api/v1
ALLOWED_ORIGINS="https://${DOMAIN}"
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_DAYS=30
MONGO_URI=mongodb://mongo:27017
MONGO_DB_NAME=company_app
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1
OLLAMA_BASE_URL=http://ollama:11434
LLM_TIMEOUT=300
LLM_MAX_RETRIES=3
MAX_TOKENS=300
LONG_TERM_MEMORY_MODEL=llama3.1
LONG_TERM_MEMORY_EMBEDDER_MODEL=nomic-embed-text
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_NUM_THREAD=${EC2_VCPUS}
OLLAMA_NUM_GPU=0
OLLAMA_FLASH_ATTENTION=1
DEFAULT_LLM_MODEL=llama3.1
DEFAULT_LLM_TEMPERATURE=0.2
RATE_LIMIT_DEFAULT="1000 per day,200 per hour"
RATE_LIMIT_CHAT="60 per minute"
RATE_LIMIT_CHAT_STREAM="60 per minute"
ENV
    log ".env.production created (JWT secret auto-generated)"
else
    log ".env.production already exists — skipping"
fi

step "6 / 8 — Set up SSL (self-signed for now)"
mkdir -p docker/ssl
if [ ! -f docker/ssl/fullchain.pem ]; then
    warn "Generating self-signed SSL certificate (replace with Let's Encrypt later)"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout docker/ssl/privkey.pem \
        -out docker/ssl/fullchain.pem \
        -subj "/C=IN/ST=Tamil Nadu/L=Chennai/O=Dilshaj Infotech/CN=${DOMAIN}" \
        -quiet 2>/dev/null
    log "Self-signed cert generated at docker/ssl/"
else
    log "SSL certs already exist"
fi

# Update nginx.conf with actual domain
sed -i "s/your-domain.com/${DOMAIN}/g" docker/nginx.conf
log "Nginx configured for domain: ${DOMAIN}"

step "7 / 8 — Build and start all services"
# Pull latest images
docker compose pull --quiet ollama mongo qdrant nginx

# Build FastAPI app image
docker compose build --no-cache app
log "App image built"

# Start infrastructure first (mongo, qdrant, ollama)
docker compose up -d mongo qdrant ollama
log "Infrastructure services started"

# Wait for Ollama to be healthy
echo -n "Waiting for Ollama to be ready"
until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo -n "."
    sleep 3
done
echo ""
log "Ollama is ready"

# Pull LLM models (this takes a while on first run)
warn "Pulling LLM models — this may take 10-20 minutes on first run"
warn "llama3.1  = 4.9 GB"
warn "nomic-embed-text = 274 MB"

docker compose run --rm ollama_puller
log "Models downloaded"

# Start app and nginx
docker compose up -d app
echo -n "Waiting for FastAPI app to pass health check"
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    echo -n "."
    sleep 5
done
echo ""
log "FastAPI app is healthy"

docker compose up -d nginx
log "Nginx started"

step "8 / 8 — Deploy summary"

echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║   ✅  Dilshaj Infotech Chatbot — Deployed Successfully!  ║${NC}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Endpoints:${NC}"
echo -e "    🌐 App       →  https://${DOMAIN}"
echo -e "    🤖 Chat UI   →  https://${DOMAIN}/static/index.html"
echo -e "    📊 Health    →  https://${DOMAIN}/health"
echo -e "    📈 Metrics   →  http://localhost:8000/metrics    (internal)"
echo -e "    🦙 Ollama    →  http://localhost:11434           (internal)"
echo ""
echo -e "  ${BOLD}Useful commands:${NC}"
echo -e "    ${YELLOW}docker compose logs -f app${NC}       → tail app logs"
echo -e "    ${YELLOW}docker compose logs -f ollama${NC}    → tail Ollama logs"
echo -e "    ${YELLOW}docker compose ps${NC}                → service status"
echo -e "    ${YELLOW}docker compose restart app${NC}       → restart app only"
echo -e "    ${YELLOW}docker compose down${NC}              → stop everything"
echo -e "    ${YELLOW}./deploy.sh${NC}                      → redeploy (updates code)"
echo ""
echo -e "  ${BOLD}Instance:${NC}  ${EC2_VCPUS} vCPUs  |  OLLAMA_NUM_THREAD=${EC2_VCPUS}"
echo ""
