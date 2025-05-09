import chainlit as cl
from chainlit.input_widget import Select, TextInput

import logging
from typing import Optional

from src.axiom.agent import AxiomAgent
from src.axiom.config import settings, load_mcp_servers_from_config
from src.axiom.prompts import AXIOM_AGENT_PROMPT, AXIOM_ASSISTANT_PROMPT

from agents.mcp import MCPServer 

# Configure logging for the UI module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants ---
SESSION_AGENT_KEY = "axiom_agent"
SESSION_HISTORY_KEY = "chat_history"
SESSION_MCP_SERVERS_KEY = "mcp_servers"

#################################
# User Authentication
#################################
@cl.oauth_callback
def oauth_callback(
  provider_id: str,
  token: str,
  raw_user_data: dict[str, str],
  default_user: cl.User,
) -> Optional[cl.User]:

  return default_user

#################################
# Quick Starter Questions
#################################
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="LangGraph Agents Creation",
            message="Create a Multi-Agent customer support system using LangGraph swarm.",
            icon="/public/msg_icons/chatbot.png",
            ),

        cl.Starter(
            label="How to use Autogent",
            message="How to use Autogen? Create some agents using Autogen",
            icon="/public/msg_icons/usb.png",
            ),
        cl.Starter(
            label="JWT Auth Implementation",
            message="How to implement JWT authentication in FastAPi? Create a complete project.",
            icon="/public/msg_icons/tools.png",
            ),

        ]
#################################
# Response modes for Axiom
#################################
@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="Agent✨",
            markdown_description= "Ideal for complex tasks like complete projects building, and full-stack apps creation."
        ),
        cl.ChatProfile(
            name="Assistant",
            markdown_description="Suited for quick information retrieval and answering questions."

        ),
    ]

#################################
# Chat Settings
#################################
@cl.on_chat_start
async def on_chat_start():
    # Initialize chat history and MCP servers
    cl.user_session.set(SESSION_HISTORY_KEY, [])
    cl.user_session.set(SESSION_MCP_SERVERS_KEY, [])

    loaded_mcp_servers: list[MCPServer] = []
    started_mcp_servers: list[MCPServer] = []

    # 1. Load MCP Server configurations
    try:
        loaded_mcp_servers = load_mcp_servers_from_config()

    except FileNotFoundError:
        await cl.ErrorMessage(content=f"Fatal Error: MCP configuration file not found at '{settings.mcp_config_path}'. Agent cannot start.").send()
        return 
    except (ValueError, Exception) as e:
        logger.exception("Failed to load MCP server configurations.")
        await cl.ErrorMessage(content=f"Fatal Error: Could not load MCP configurations: {e}. Agent cannot start.").send()
        return 

    # 2. Start the loaded MCP servers sequentially
    if loaded_mcp_servers:
        for server in loaded_mcp_servers:
            try:
                logger.info(f"Starting MCP Server: {server.name}...")
                # The __aenter__ starts the server process
                await server.__aenter__() 
                started_mcp_servers.append(server)
                logger.info(f"MCP Server '{server.name}' started successfully.")
            except Exception as e:
                logger.error(f"Failed to start MCP Server '{server.name}': {e}")

        # Store only the successfully started servers for later cleanup
        cl.user_session.set(SESSION_MCP_SERVERS_KEY, started_mcp_servers) 

#################################
# MCP Server Cleanup
#################################
async def cleanup_mcp_servers():
    started_mcp_servers = cl.user_session.get(SESSION_MCP_SERVERS_KEY, [])
    if not started_mcp_servers:
        return

    logger.info(f"Cleaning up {len(started_mcp_servers)} MCP server(s)...")
    for server in started_mcp_servers:
        try:
            await server.__aexit__(None, None, None) 
            logger.info(f"MCP Server '{server.name}' stopped.")
        except Exception as e:
            logger.error(f"Error stopping MCP Server '{server.name}': {e}", exc_info=True) 
    
    cl.user_session.set(SESSION_MCP_SERVERS_KEY, []) # Clear the list

@cl.on_chat_end
async def on_chat_end():
    logger.info("Chat session ending.")
    await cleanup_mcp_servers()

#################################
# User Message Handler
#################################
@cl.on_message
async def on_message(message: cl.Message):
    started_mcp_servers = cl.user_session.get(SESSION_MCP_SERVERS_KEY)
    chat_history: list[dict] = cl.user_session.get(SESSION_HISTORY_KEY, []) 
    
    # Initialize the Axiom Agent
    axiom_mode = cl.user_session.get("chat_profile")
    
    # Filter MCP servers based on chat profile
    if axiom_mode == "Assistant":
        # For Assistant mode, only use context7 MCP server
        filtered_servers = [server for server in started_mcp_servers if server.name.lower() == "context7"]
    else:
        # For Agent mode, use all MCP servers
        filtered_servers = started_mcp_servers

    agent = AxiomAgent(
        model=settings.DEFAULT_AGENT_MODEL if axiom_mode == "Agent✨" else settings.DEFAULT_ASSISTANT_MODEL,
        mcp_servers=filtered_servers,
        prompt=AXIOM_AGENT_PROMPT if axiom_mode == "Agent✨" else AXIOM_ASSISTANT_PROMPT,
        )

    # Add user message to history
    chat_history.append({"role": "user", "content": message.content})
    
    msg = cl.Message(content="")
    full_response = ""

    try:
        response = agent.stream_agent(chat_history)
        async for token in response:
            full_response += token
            await msg.stream_token(token) # Stream tokens to the UI
        # Send the final message
        await msg.send()
    except Exception as e:
        logger.exception(f"Error during agent response streaming: {e}")
        # Update the message placeholder with an error
        await msg.update(content=f"Sorry, an error occurred while processing your request.") 
        chat_history.append({"role": "assistant", "content": f"[Agent Error Occurred]"}) 
    else:
        # Only append successful response if no exception occurred
        chat_history.append({"role": "assistant", "content": full_response})
    finally:
        # Update session history
        cl.user_session.set(SESSION_HISTORY_KEY, chat_history)

