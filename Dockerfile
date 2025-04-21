# Use the official Python 3.11 slim image as the base
FROM python:3.1-slim

# --- Install System Dependencies, uv, and Node.js/npm/npx ---
# Install curl (for uv script), nodejs & npm (for npx), git (optional, but sometimes needed by deps)
# Install uv using its official script
# Install npx globally using npm (often included with recent npm, but explicit install is safer)
# Clean up apt cache to reduce image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl nodejs npm git && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    # mv /root/.local/bin/uvx /usr/local/bin/uvx # uvx might not be needed unless you use uv run directly
    npm install -g npx && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# --- Python Dependency Installation (as root for system-wide access) ---
# Create cache directory for uv
RUN mkdir -p /.cache/uv

# Copy only the pyproject.toml file first to leverage Docker layer caching
COPY pyproject.toml .

# Install Python dependencies using uv sync based on pyproject.toml
# This reads dependencies and installs them efficiently
# Remove the uv cache after installation if not needed later to save space
RUN uv sync --system && \
    rm -rf /.cache/uv/*

# --- Non-Root User Setup ---
# Create a non-root user 'user' with ID 1000 and create their home directory
# Note: Cache was already cleaned, so no need to chown it here.
RUN useradd -m -u 1000 user
# Switch to the non-root user
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
# If you have a .env file for local dev, ensure it's NOT copied (use .dockerignore)
# Secrets should come from Hugging Face Secrets management

# --- Runtime ---
# Expose the port Chainlit will run on (standard HF Spaces port)
EXPOSE 7860

# Define the command to run the Chainlit application
# Listen on all interfaces (0.0.0.0) on the designated port
# Do NOT use the --watch (-w) flag in production
CMD ["chainlit", "run", "chainlit_ui.py", "--host", "0.0.0.0", "--port", "7860"]