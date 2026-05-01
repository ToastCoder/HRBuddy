import json
import os
from core.logger import log

def load_config():
    """
    Reads the JSON config path from the environment variable 
    set in your run.sh script.
    """
    # This variable is set in your run.sh based on your laptop (M5 vs Kubuntu)
    config_path = os.getenv("HRBUDDY_CONFIG", "config/apple_mlx_config.json")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            config["ollama_base_url"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            log.info(f"Configuration loaded from {config_path}")
            return config
    except FileNotFoundError:
        log.error(f"Config file NOT FOUND at {config_path}. Check your run.sh paths.")
        return {}
    except Exception as e:
        log.error(f"Unexpected error loading config: {e}")
        return {}

cfg = load_config()