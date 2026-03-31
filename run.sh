#!/bin/bash

# Variables
PKG_MGR="pip"
FILE="dependencies.txt"

# Check for dependency file
if [ ! -f "$FILE" ]; then
    echo "[ERROR] '$FILE' not found."
    exit 1
fi

echo "[OK] dependencies.txt found"

# Parser for choosing Package Manager (pip or conda)
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -m)
            PKG_MGR="$2"
            shift 2
            ;;

        *)
            echo "[ERROR] Unknown Option: $1. Usage ./run.sh [-m pip | conda]"
            exit 1
            ;;
    esac
done

echo "[INFO] Selected Package Manager: '$PKG_MGR'"

# Install Dependencies
if [ "$PKG_MGR" == "conda" ]; then
    echo "[OK] Starting installation using Conda..."
    conda install --file "$FILE" -c conda-forge -y

elif [ "$PKG_MGR" == "pip" ]; then
    echo "[OK] Starting installation using Pip..."
    pip install -r "$FILE"

else
    echo "[Error] Invalid manager '$PKG_MANAGER'. Please use 'pip' or 'conda'."
    exit 1
fi

# Check for Ollama
echo "[INFO] Verifying Python environment binding..."
if ! python3 -c "import ollama" &> /dev/null; then
    echo "[WARNING] Python cannot find 'ollama' library. Forcing strict inline installation..."
    python3 -m pip install ollama
    
    if [ $? -ne 0 ]; then
        echo "[ERROR] Could not force-install Python ollama library."
        exit 1
    fi
    echo "[OK] 'ollama' bound to current Python environment."
else
    echo "[OK] Python recognizes 'ollama'."
fi

# System Ollama Engine Check and Install
echo "[INFO] Checking system Ollama engine..."
if ! command -v ollama &> /dev/null; then
    echo "[WARNING] Ollama engine not found. Installing now (may require password)..."
    curl -fsSL https://ollama.com/install.sh | sh
    
    if [ $? -ne 0 ]; then
        echo "[ERROR] Ollama engine installation failed."
        exit 1
    fi
    echo "[OK] Ollama engine installed successfully."
else
    echo "[OK] Ollama engine is already installed."
fi

# Required Models for RAG
echo "[INFO] Verifying AI models (TinyLlama & Nomic)..."
ollama pull tinyllama
ollama pull nomic-embed-text
echo "[OK] All models are ready."

# Start Application
echo "[INFO] Starting RAG application..."
python3 main.py