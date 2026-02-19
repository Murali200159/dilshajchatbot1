# Deploying to AWS EC2 (Ubuntu) with Ollama

This guide will walk you through deploying the project to an AWS EC2 instance. Follow these steps exactly to ensure a smooth deployment.

## 1. Instance Setup
1.  **Launch Instance**:
    - **OS**: Ubuntu Server 24.04 LTS (or 22.04 LTS).
    - **Instance Type**: `t3.xlarge` (4 vCPU, 16GB RAM) or `g4dn.xlarge` (if you need GPU acceleration).
    - **Storage**: At least 50GB gp3 root volume.

2.  **Security Group (Firewall)**:
    - **Inbound Rules**:
        - **SSH (22)**: My IP (for your access).
        - **TCP (8000)**: Anywhere `0.0.0.0/0` (for the API/App).
        - **TCP (11434)**: **Custom** -> Allow from `172.17.0.0/16` (Docker Network) or `0.0.0.0/0` if testing (Restrict in production!).

## 2. Install Docker & Utilities
Connect to your instance via SSH:
```bash
ssh -i "your-key.pem" ubuntu@your-ec2-ip
```

Run the following commands to install Docker and Git:
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y docker.io docker-compose-v2 git curl
sudo usermod -aG docker $USER
newgrp docker

# Verify Docker is running
docker run hello-world
```

## 3. Install & Configure Ollama
We will run Ollama on the **host** (the EC2 instance itself) so it can access CPU/GPU resources directly, but we need to configure it to listen on all interfaces so the Docker container can talk to it.

1.  **Install Ollama**:
    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ```

2.  **Configure Ollama to Listen on All Interfaces**:
    By default, Ollama only listens on `127.0.0.1`. We need it on `0.0.0.0` so the Docker container (running the app) can reach it.
    
    Edit the systemd service file:
    ```bash
    sudo systemctl edit ollama.service
    ```
    
    Add the following lines in the editor that opens:
    ```ini
    [Service]
    Environment="OLLAMA_HOST=0.0.0.0"
    ```
    
    Save and exit (Ctrl+O, Enter, Ctrl+X).

3.  **Restart Ollama**:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl restart ollama
    ```

4.  **Pull the Model**:
    ```bash
    ollama pull llama3:latest
    # Or your custom model if you have one
    ```

## 4. Deploy the Application
1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd fastapi-langgraph-agent-production-ready-template-master
    ```

2.  **Configure Environment**:
    ```bash
    cp .env.example .env
    nano .env
    ```
    
    **CRITICAL CHANGE**: Ensure this line is set in your `.env` file:
    ```ini
    # This points to the host machine from inside the Docker container
    OLLAMA_BASE_URL=http://host.docker.internal:11434
    APP_ENV=production
    ```

3.  **Start the Application**:
    ```bash
    docker compose up -d --build
    ```

4.  **View Logs** (to ensure no errors):
    ```bash
    docker compose logs -f app
    ```

## 5. Verify Deployment
Open your browser and navigate to:
- **Frontend**: `http://<your-ec2-ip>:8000/`
- **API Docs**: `http://<your-ec2-ip>:8000/docs`

## Troubleshooting
- **"Connection Refused" to Ollama**:
    - Run `netstat -tuln | grep 11434` on the host. It MUST show `0.0.0.0:11434` or `:::11434`. If it shows `127.0.0.1:11434`, you missed step 3.2.
- **Docker Permission Denied**:
    - Run `newgrp docker` or reboot the instance.
- **MongoDB Connection Failed**:
    - Check logs: `docker compose logs mongodb`. The app will wait for MongoDB to be healthy before starting.
