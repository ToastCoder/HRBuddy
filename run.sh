#!/bin/bash

# nstall/Check Docker Engine
if ! command -v docker &> /dev/null; then
    echo "[INFO] Docker not found. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "[OK] Docker installed. Note: You may need to reboot for permissions."
else
    echo "[OK] Docker is already installed."
fi

# Ensure Docker service is active
sudo systemctl start docker
sudo systemctl enable docker &> /dev/null

# Install/Check Ollama Engine
if ! command -v ollama &> /dev/null; then
    echo "[INFO] Ollama not found. Installing..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "[OK] Ollama is already installed."
fi

# Patch Ollama for Docker Networking
# Allows the container to communicate with the host machine
CONF_DIR="/etc/systemd/system/ollama.service.d"
CONF_FILE="$CONF_DIR/override.conf"

if [ ! -f "$CONF_FILE" ]; then
    echo "[INFO] Patching Ollama to allow Docker connections..."
    sudo mkdir -p "$CONF_DIR"
    echo -e "[Service]\nEnvironment=\"OLLAMA_HOST=0.0.0.0\"" | sudo tee "$CONF_FILE" > /dev/null
    sudo systemctl daemon-reload
    sudo systemctl restart ollama
    echo "[OK] Ollama network patch applied."
fi

# Pull AI Models
echo "[INFO] Syncing AI models..."
ollama pull llama3.2
ollama pull nomic-embed-text
echo "[OK] Models are ready."

# Launch Docker Compose
echo "[INFO] Building and Launching Containers..."

# Try 'docker compose' first, fallback to 'docker-compose'
if docker compose version &> /dev/null; then
    docker compose up --build
else
    docker-compose up --build
fi