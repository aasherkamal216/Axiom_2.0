from typing import Optional
from typing_extensions import AsyncGenerator

from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent

from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    Tool,
)
from agents.mcp import MCPServer

from .config import settings
from .prompts import AXIOM_AGENT_PROMPT

class AxiomAgent:
    def __init__(
        self,
        model: Optional[str] = None,
        tools: Optional[list[Tool]] = None,
        mcp_servers: Optional[list[MCPServer]] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self._api_key = api_key or settings.GOOGLE_API_KEY
        self.base_url = base_url or settings.BASE_URL
        self.model_name = model or settings.DEFAULT_MODEL
        
        self._client: AsyncOpenAI = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self.base_url,
        )

        self.agent = Agent(
            name=settings.AGENT_NAME,
            instructions=AXIOM_AGENT_PROMPT or "You are a helpful assistant.",
            mcp_servers=mcp_servers or [],
            tools=tools or [],
        )

    def _get_run_config(self) -> RunConfig:

        # Create the specific model configuration
        model_instance = OpenAIChatCompletionsModel(
            model=self.model_name,
            openai_client=self._client
        )

        return RunConfig(
            model=model_instance,
            tracing_disabled=not settings.TRACING_ENABLED,
        )

    async def run_agent(self, chat_history: str | list[dict[str, str]]) -> str:
        """
        Runs the agent with the given chat history and returns the final response.

        Args:
            chat_history: A list of message dictionaries (e.g., [{"role": "user", "content": "Hi"}]).

        Returns:
            The final text output from the agent.
        """
        config = self._get_run_config()

        try:
            result = await Runner.run(
                starting_agent=self.agent,
                input=chat_history,
                run_config=config
            )
            return result.final_output

        except Exception as e:
            return f"An error occurred during processing: {e}"

    async def stream_agent(self, chat_history: str | list[dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Runs the agent with the given chat history and streams the response tokens.

        Args:
            chat_history: A list of message dictionaries.

        Yields:
            String tokens of the agent's response.
        """ 
        config = self._get_run_config()

        try:
            result = Runner.run_streamed(
                starting_agent=self.agent,
                input=chat_history,
                max_turns=20,
                run_config=config
            )
            async for event in result.stream_events():
                if (event.type == "raw_response_event" and 
                    isinstance(event.data, ResponseTextDeltaEvent)):
                    if token := event.data.delta:
                        yield token
        
        except Exception as e:
            yield f"\n[Error during streaming: {e}]\n"