# System MongoDB Engine Check & Install
echo "[INFO] Checking for MongoDB..."
if ! command -v mongod &> /dev/null && ! command -v mongo &> /dev/null; then
    echo "[WARNING] MongoDB not found. Detecting OS to install..."
    
    # Detect the operating system
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case "$ID_LIKE" in
            *fedora*|*rhel*|*centos*)
                echo "[INFO] Detected RedHat/Fedora base. Installing via dnf..."
                sudo dnf install -y mongodb-server
                SVC_NAME="mongod"
                ;;
            *debian*|*ubuntu*)
                echo "[INFO] Detected Debian/Ubuntu base. Installing via apt..."
                sudo apt-get update
                sudo apt-get install -y mongodb
                SVC_NAME="mongodb"
                ;;
            *archlinux*)
                echo "[INFO] Detected Arch base. Installing via pacman..."
                sudo pacman -S --noconfirm mongodb
                SVC_NAME="mongodb"
                ;;
            *)
                echo "[ERROR] Auto-install for this OS is not supported. Please install MongoDB manually."
                exit 1
                ;;
        esac
        
        echo "[OK] MongoDB installed successfully."
        
        # Automatically enable and start the background service
        echo "[INFO] Starting MongoDB service..."
        sudo systemctl enable --now $SVC_NAME
    else
        echo "[ERROR] Could not detect OS. Please install MongoDB manually."
        exit 1
    fi
else
    echo "[OK] MongoDB is already installed."
    
    # Ensure the service is actually awake and running
    if ! systemctl is-active --quiet mongod && ! systemctl is-active --quiet mongodb; then
         echo "[INFO] Waking up stopped MongoDB service..."
         sudo systemctl start mongod || sudo systemctl start mongodb
    fi
fi