#!/bin/bash

set -e # Exit on error

# Detecting the Operating System
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Ensure Docker is actually running before trying to connect
    if ! docker info > /dev/null 2>&1; then
        echo "[INFO] Docker Desktop is not running. Launching it now..."
        open -a Docker
        echo "Please wait for Docker to start, then re-run this script."
        exit 1
    fi
    # Set the host variable to the standard macOS socket location
    export DOCKER_HOST="unix:///var/run/docker.sock"

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo "[INFO] Running on Linux"
else
    echo "[ERROR] Unsupported OS. Exiting."
    exit 1
fi

# Check and install Docker
if ! command -v docker &> /dev/null; then
    echo "[INFO] Docker not found. Installing..."
    if [ "$OS" == "macos" ]; then
        # Check for Homebrew first
        if ! command -v brew &> /dev/null; then
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install --cask docker # Installs Docker Desktop
        echo "[ACTION] Please open Docker from your Applications folder to finish setup."
        open /Applications/Docker.app
    else
        curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
        sudo usermod -aG docker $USER
    fi
else
    echo "[OK] Docker is already installed."
fi

# Check and Install Ollama
if ! command -v ollama &> /dev/null; then
    echo "[INFO] Ollama not found. Installing..."
    if [ "$OS" == "macos" ]; then
        brew install ollama
    else
        curl -fsSL https://ollama.com/install.sh | sh
    fi
else
    echo "[OK] Ollama is already installed."
fi

# Patch Ollama for Docker Networking
if [ "$OS" == "linux" ]; then
    CONF_DIR="/etc/systemd/system/ollama.service.d"
    if [ ! -d "$CONF_DIR" ]; then
        sudo mkdir -p "$CONF_DIR"
        echo -e "[Service]\nEnvironment=\"OLLAMA_HOST=0.0.0.0\"" | sudo tee "$CONF_DIR/override.conf" > /dev/null
        sudo systemctl daemon-reload && sudo systemctl restart ollama
    fi

elif [ "$OS" == "macos" ]; then
    export OLLAMA_HOST=0.0.0.0
    launchctl setenv OLLAMA_HOST "0.0.0.0"
    echo "[OK] macOS Ollama host set to 0.0.0.0"
fi

# Pull AI Models
echo "[INFO] Pulling AI models..."
ollama serve > /dev/null 2>&1 & 
sleep 5
ollama pull llama3.2
ollama pull nomic-embed-text

# Launch Docker Compose
echo "[OK] Models ready."
echo "[INFO] Building and Launching HRBuddy Containers..."
docker compose up --build