# Axiom 2.0 - Advanced AI Development Agent

![AxiomAgent Image](/public/axiom.png) <!-- Assuming this image exists in public/ -->

Axiom 2.0 is an **advanced AI Agent** built to assist developers in navigating the complex landscape of modern AI and software development. Leveraging the **OpenAI Agents SDK**, **Model Context Protocol (MCP)**, Chainlit, and Gemini models, Axiom 2.0 specializes in generating accurate, production-ready code and providing expert guidance across areas like agent architectures, RAG systems, authentication, vector databases, and full-stack development.

Axiom 2.0 is an upgrade of Axiom 1.0, it has the following more features:
1. **Production-Ready Code Focus:** Axiom 2.0's primary goal is to generate production-quality, modular, efficient, scalable, and readable code, including end-to-end projects and full-stack applications.
2. **Vast Library Database:** It has access to a vast library database (**2000+** libraries, frameworks, and tools) unlike it's predecessor, Axiom 1.0 which had only 20 libraries documentation.

## Features

*   🤖 **Interactive Chat Interface:** Built with Chainlit for a smooth conversational experience.
*   📚 **Advanced Documentation Access:** Utilizes a dedicated MCP server to retrieve and apply technical information from various sources, ensuring code and explanations are accurate and up-to-date.
*   🧪 **Two Modes:** 
    1. **Agent Mode:** Ideal for complex tasks like end-to-end projects and full-stack development.
    2. **Assistant Mode:** Suited for quick information retrieval and answering questions.
*   🧠 **Web Search:** It uses Tavily MCP server to search the web and extract content from URLs.
*   📦 **Containerized Deployment:** Includes a `Dockerfile` for easy deployment to platforms like Hugging Face Spaces or Docker environments.


## How it Works

Axiom 2.0 operates using the OpenAI Agents SDK. MCP servers are integrated as specialized tools:

1.  **Configuration (`mcp.json`):** The `mcp.json` file in the project root defines the MCP servers (like the Context7 and Tavily servers).
2.  **Agent Initialization:** When the Chainlit application starts, it reads `mcp.json`, initializes the specified `MCPServerStdio` instances, and attempts to start their underlying processes.
3.  **Response Integration:** The MCP server performs its task (e.g., searching documentation, searching web) and sends the result back to the agent via the SDK. The agent then uses this information to formulate its final response to the user.

## Prerequisites

*   **Python 3.11+:** The project requires Python 3.11 or later.
*   **UV Package Manager:** Used for dependency management. Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`.
*   **Google Gemini API Key:** Required to use the Gemini models via the OpenAI API endpoint.
*   **Node.js and npm/npx:** Required locally *only if you need to run the MCP servers manually for debugging*. The Dockerfile handles installing this for deployment.
*   **Docker (Optional):** If you intend to use the `Dockerfile` for containerized deployment.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/aasherkamal216/Axiom_2.0.git
    cd Axiom_2.0
    ```

2.  **Create and Activate Virtual Environment using UV:**
    ```bash
    uv venv
    # For Windows
    .venv\Scripts\activate
    # For macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    uv sync
    ```

4.  **Set up environment variables:**
    ```bash
    cp .env.example .env
    ```
    Add your API keys and other credentials in `.env` file. 

## Configuration

*   **Config File:** All the configuration is handled in the `src/axiom/config.py` file. Change the values in this file to modify the configuration.
*   **MCP Servers:** Defined in the `mcp.json` file in the project root. This file specifies which MCP servers the agent will attempt to load and their startup commands. Modify this file to add, remove, or change MCP server configurations.

## Usage

**Run the Chainlit application:**
The Chainlit application will automatically load and attempt to start the MCP servers defined in `mcp.json` on chat start.
    
```bash
uv run chainlit run chainlit_ui.py -w
```
The `-w` flag enables auto-reloading during development. For production, omit `-w`. The application will be available at `http://localhost:8000`.

## Docker Deployment

1.  **Build the Docker image:**
    Navigate to the project root in your terminal.
    ```bash
    docker build -t axiom-2.0 .
    ```

2.  **Run the Docker container:**
    Map the container's port 7860 (where Chainlit runs) to a port on your host machine (e.g., 7860).
    ```bash
    docker run -p 7860:7860 -p 8082:8082 axiom-2.0
    ```
