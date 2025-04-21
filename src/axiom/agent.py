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

from types import AsyncGeneratorType

class AxiomAgent:
    def __init__(
        self,
        model: str | None = None,
        tools: list[Tool] | None = None,
        mcp_servers: list[MCPServer] | None = None,
    ):
        self._api_key = settings.GOOGLE_API_KEY
        self.base_url = settings.BASE_URL
        self.model = model if model else settings.DEFAULT_MODEL

        self.agent = Agent(
            name="Axiom 2.0",
            instructions=AXIOM_AGENT_PROMPT,
            mcp_servers=mcp_servers,
            tools=tools,
        )

    def _get_model_config(self):

        client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self.base_url,
        )
        model = OpenAIChatCompletionsModel(model=self.model, openai_client=client)
        return RunConfig(
            model=model,
            model_provider=client,
            tracing_disabled=True,
        )

    async def run_agent(self, input: str | list[dict[str, str]]):
        config = self._get_model_config()

        result = await Runner.run(
            starting_agent=self.agent,
            input=input,
            run_config=config
        )
        return result.final_output

    async def stream_agent(self, input: str | list[dict[str, str]]) -> AsyncGenerator:
        config = self._get_model_config()

        result = await Runner.run_streamed(
            starting_agent=self.agent,
            input=input,
            run_config=config
        )
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                if token:= event.data.delta or "":
                    yield token