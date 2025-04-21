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
            name="Axiom 2.0",
            instructions=AXIOM_AGENT_PROMPT,
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
            tracing_disabled=True,
        )

    async def run_agent(self, input: str | list[dict[str, str]]):
        config = self._get_run_config()

        result = await Runner.run(
            starting_agent=self.agent,
            input=input,
            run_config=config
        )
        return result.final_output

    async def stream_agent(self, input: str | list[dict[str, str]]) -> AsyncGenerator:
        config = self._get_run_config()

        result = Runner.run_streamed(
            starting_agent=self.agent,
            input=input,
            run_config=config
        )
        async for event in result.stream_events():
            if (event.type == "raw_response_event" and 
                isinstance(event.data, ResponseTextDeltaEvent)):
                if token := event.data.delta:
                    yield token