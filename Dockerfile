# Use the official Python 3.12 slim image as the base
FROM python:3.12-slim

# --- Install System Dependencies, uv, and Node.js/npm/npx ---
# Install curl (for uv script), nodejs & npm (for npx), git (optional, but sometimes needed by deps)
# Install uv using its official script
# Install npx globally using npm (often included with recent npm, but explicit install is safer)
# Clean up apt cache to reduce image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl git ca-certificates gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    NODE_MAJOR=20 && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install nodejs -y && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# --- Python Dependency Installation (as root for system-wide access) ---
# Create cache directory for uv
RUN mkdir -p /.cache/uv

# Copy only the pyproject.toml file first to leverage Docker layer caching
COPY pyproject.toml ./
COPY README.md ./

# Install Python packages as root using uv sync
RUN uv sync && \
    rm -rf /.uv

# Create and switch to non-root user
RUN useradd -m -u 1000 user && \
    chown -R user:user /.cache/uv

USER user

# --- Environment Setup ---
# Set the home directory for the user
ENV HOME=/home/user
# Add user's local bin to PATH (though we installed system-wide with uv sync --system)
# Ensure Python output is sent straight to terminal without being buffered
# Set the default port expected by Hugging Face Spaces for web apps
ENV PATH="/home/user/.local/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=7860

# Set the working directory for the application inside the user's home
WORKDIR $HOME/app

# --- Application Code ---
# Copy the rest of the application files needed at runtime
# Ensure the non-root user owns these files
# Specific copies are better for caching than 'COPY . .' after dependency install
COPY --chown=user:user ./chainlit_ui.py ./chainlit_ui.py
COPY --chown=user:user ./mcp.json ./mcp.json
COPY --chown=user:user ./src ./src
COPY --chown=user:user ./public ./public
COPY --chown=user:user ./chainlit.yaml ./chainlit.yaml
COPY --chown=user:user ./chainlit.md ./chainlit.md

# --- Runtime ---
# Expose the port Chainlit will run on (standard HF Spaces port)
EXPOSE 7860

# Define the command to run the Chainlit application
# Listen on all interfaces (0.0.0.0) on the designated port
# Do NOT use the --watch (-w) flag in production
CMD ["uv","run", "chainlit", "run", "chainlit_ui.py", "--host", "0.0.0.0", "--port", "7860"]