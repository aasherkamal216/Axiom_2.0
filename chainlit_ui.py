import chainlit as cl

from agents.mcp import MCPServerStdio
from src.axiom.agent import AxiomAgent

@cl.on_chat_start 
async def on_chat_start():

    server1 = MCPServerStdio(
        name="Documentation MCP",
        params={
            "command": "npx",
            "args": ['-y', '@upstash/context7-mcp@latest']
        },
    )
    server2 = MCPServerStdio(
        name="Sequential Thinking MCP",
        params={
            "command": "npx",
            "args": ['-y', '@modelcontextprotocol/server-sequential-thinking']
        },
    )
    try:
         # Manually enter the async context
        await server1.__aenter__()
        await server2.__aenter__() 
    except Exception as e:
        cl.Message(content=f"Failed to start MCP Server: {e}").send()
        return

    agent = AxiomAgent(mcp_servers=[server1, server2])
    cl.user_session.set("axiom_agent", agent)
    cl.user_session.set("chat_history", [])

@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("axiom_agent")
    chat_history = cl.user_session.get("chat_history")
    # Add user message to history
    chat_history.append({"role": "user", "content": message.content})
    cl.user_session.set("chat_history", chat_history)

    response_generator = agent.stream_agent(chat_history)

    full_response = ""
    msg = cl.Message(content="") # Initialize an empty message for streaming

    async for token in response_generator:
        full_response += token
        await msg.stream_token(token) # Stream tokens to the UI
    await msg.send() # Send the final message

    chat_history.append({"role": "assistant", "content": full_response})
    cl.user_session.set("chat_history", chat_history) # Update chat history
