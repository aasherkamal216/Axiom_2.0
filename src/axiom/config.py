import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from agents.mcp import MCPServer, MCPServerStdio

_ = load_dotenv()

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Determine Project Root ---
PROJECT_ROOT = Path(__file__).parent.parent.parent 

# --- MCP Server Configuration Model ---
class MCPServerConfig(BaseSettings):
    """Represents the configuration for a single MCP server in mcp.json."""
    command: str
    args: List[str]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )
    """
    Configuration settings for the Axiom 2.0 Agent.
    """
    # --- API Configuration ---
    GOOGLE_API_KEY: str
    DEFAULT_MODEL: str = "gemini-2.0-flash"
    BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    
    # --- Model Configuration ---
    AVAILABLE_MODELS: list[str] = [
        "gemini-2.0-flash", 
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash-thinking-exp-1219",
        "gemini-2.5-pro-exp-03-25",
        "gemini-2.5-flash-preview-04-17",
    ]

    # --- Agent Configuration ---
    AGENT_NAME: str = "Axiom 2.0"
    MAX_DOCS_TOKEN_LIMIT: int = 20000  # Maximum tokens to retrieve from the documentations
    
    # --- Tracing ---
    TRACING_ENABLED: bool = False

    # --- MCP Configuration ---
    MCP_CONFIG_PATH: Path = Field(default=PROJECT_ROOT / "mcp.json")

# --- Instantiate Settings ---
try:
    settings = Settings()
    if not settings.GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY is not set. OpenAI client initialization might fail.")
except ValidationError as e:
    logger.error(f"Configuration validation failed: {e}")
    raise SystemExit(f"Configuration error: {e}") from e


# --- MCP Server Loading Function ---
def load_mcp_servers_from_config(config_path: Path = settings.MCP_CONFIG_PATH) -> List[MCPServer]:
    """
    Loads MCP server configurations from the specified JSON file.
    """
    servers: List[MCPServer] = []
    
    # Raise FileNotFoundError if file doesn't exist
    if not config_path.is_file():
        logger.error(f"MCP configuration file not found: {config_path}")
        raise FileNotFoundError(f"MCP configuration file not found: {config_path}")

    # Allow json.JSONDecodeError to propagate if file is invalid JSON
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mcp_servers_data = data.get("mcpServers")
    if not isinstance(mcp_servers_data, dict):
        # Raise ValueError if the main structure is wrong
        raise ValueError("Invalid mcp.json structure: 'mcpServers' key must map to an object.")

    # Iterate and handle individual server errors as warnings
    for name, config_dict in mcp_servers_data.items():
        try:
            server_config = MCPServerConfig(**config_dict) 
            
            server_instance = MCPServerStdio(
                    name=name,
                    params={
                        "command": server_config.command,
                        "args": server_config.args,
                    }
                )
            servers.append(server_instance)

        except (ValidationError, Exception) as e:
            logger.warning(f"Skipping MCP server '{name}' due to configuration error: {e}")

    return servers