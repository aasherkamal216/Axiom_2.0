import asyncio
from typing import List, Dict, Optional

from src.axiom.agent import AxiomAgent
from src.axiom.config import settings, load_mcp_servers_from_config 
from agents.mcp import MCPServer 
import logging

# --- Configure Logging ---
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING) 

# Use Rich for pretty output
from rich.console import Console
from rich.markdown import Markdown
from rich.rule import Rule
from rich.text import Text

console = Console()

async def get_user_input(prompt_text: str) -> str:
    """Gets user input asynchronously with a styled prompt."""
    # Render the prompt text using Rich
    prompt_markup = Text.from_markup(prompt_text, style="bold blue")
    return await asyncio.to_thread(console.input, prompt_markup)


async def main():
    console.print(Rule("[bold blue] Welcome to Axiom CLI [/bold blue]", style="blue"))
    console.print("[dim]Type 'quit' or 'exit' to end the chat.[/dim]")
    console.print("") # Blank line

    loaded_mcp_servers: List[MCPServer] = []
    started_mcp_servers: List[MCPServer] = []
    agent: Optional[AxiomAgent] = None
    chat_history: List[Dict[str, str]] = []

    try:
        # 1. Load MCP Servers
        console.print("[bold]Loading MCP configurations...[/bold]")
        try:
            loaded_mcp_servers = load_mcp_servers_from_config()
            if loaded_mcp_servers:
                 console.print(f"[green]Loaded {len(loaded_mcp_servers)} server(s) config.[/green] Attempting to start...")
            else:
                 console.print("[yellow]No MCP server configurations found or loaded.[/yellow]")

        except Exception as e:
            console.print(f"[bold red]Error loading MCP config:[/bold red] [red]{e}[/red]")

        # 2. Start MCP Servers
        if loaded_mcp_servers:
            for server in loaded_mcp_servers:
                try:
                    await server.__aenter__()
                    started_mcp_servers.append(server)
                    console.print(f"  [green]Started:[/green] {server.name}")
                except Exception as e:
                    console.print(f"  [yellow]Failed to start:[/yellow] {server.name} - [yellow]{e}[/yellow]")

        if loaded_mcp_servers and not started_mcp_servers:
             console.print("[yellow]Warning: All configured MCP servers failed to start. Agent will operate without MCP tools.[/yellow]")
        elif started_mcp_servers:
             console.print(f"[green]Successfully started {len(started_mcp_servers)} MCP server(s).[/green]")

        # 3. Initialize the Agent
        console.print("[bold]Initializing Agent...[/bold]")
        try:
            agent = AxiomAgent(mcp_servers=started_mcp_servers)
            console.print(f"[bold green]{settings.AGENT_NAME} is ready![/bold green]")
        except Exception as e:
            console.print(f"[bold red]Fatal Error: Could not initialize Agent:[/bold red] [red]{e}[/red]")
            raise

        console.print(Rule(style="blue"))

        # 4. Main chat loop
        while True:
            # Get user input with styled prompt
            user_input = await get_user_input("You: ")

            if user_input.lower() in ['quit', 'exit']:
                break

            chat_history.append({"role": "user", "content": user_input})

            console.print("[bold green]Axiom:[/bold green]") # Print Agent prefix before response

            full_response = ""
            # Use Rich Status for the thinking indicator while streaming
            with console.status("[bold green]Thinking...[/bold green]", spinner="dots", speed=0.5) as status:
                 try:
                    response_generator = agent.stream_agent(chat_history)
                    async for token in response_generator:
                        full_response += token
                    status.stop()

                 except Exception as e:
                     status.stop()
                     console.print(f"\n[bold red]Error during response:[/bold red] [red]{e}[/red]", style="red")
                     full_response = f"[Error: {e}]"


            # Render the full response using Markdown
            if full_response:
                 console.print(Markdown(full_response)) # Renders code blocks, lists, etc.
            else:
                 console.print("[dim](No response generated)[/dim]")

            chat_history.append({"role": "assistant", "content": full_response})
            console.print(Rule(style="blue")) # Print a rule after each turn

    except Exception as e:
        # Catch any unexpected errors from Agent init or loop setup
        console.print(f"\n[bold red]An unhandled error occurred:[/bold red] [red]{e}[/red]", style="red", highlight=True)

    finally:
        # 5. Cleanup: Stop MCP Servers
        if started_mcp_servers:
            console.print(Rule("[dim]Stopping MCP servers[/dim]", style="blue"))
            for server in started_mcp_servers:
                try:
                    await server.__aexit__(None, None, None)
                    console.print(f"  [dim]Stopped:[/dim] {server.name}")
                except Exception as e:
                    console.print(f"  [red]Error stopping:[/red] {server.name} - [red]{e}[/red]")

        console.print(Rule("[bold blue] Chat ended. Goodbye! [/bold blue]", style="blue"))

if __name__ == "__main__":
    asyncio.run(main())