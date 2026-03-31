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
    conda install --file "$FILE" -y

elif [ "$PKG_MGR" == "pip" ]; then
    echo "[OK] Starting installation using Pip..."
    pip install -r "$FILE"

else
    echo "[Error] Invalid manager '$PKG_MANAGER'. Please use 'pip' or 'conda'."
    exit 1
fi