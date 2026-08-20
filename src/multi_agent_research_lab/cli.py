"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def _parse_query(query: str) -> ResearchQuery:
    try:
        return ResearchQuery(query=query)
    except ValidationError as exc:
        console.print(
            Panel.fit(
                f"Invalid query: {exc.errors()[0]['msg']}",
                title="Input Error",
                style="red",
            )
        )
        raise typer.Exit(code=1) from exc


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline placeholder."""

    from multi_agent_research_lab.services.search_client import SearchClient
    from multi_agent_research_lab.services.llm_client import LLMClient
    import time
    
    _init()
    request = _parse_query(query)
    state = ResearchState(request=request)
    
    search_client = SearchClient()
    llm_client = LLMClient()
    
    start_time = time.time()
    
    try:
        # Search
        sources = search_client.search(request.query, max_results=request.max_sources)
        state.sources = sources
        sources_text = "\n".join([f"[{i+1}] {s.title} - {s.url}" for i, s in enumerate(sources)])
        
        # LLM
        system_prompt = f"You are a helpful assistant. Answer the user's query based on the following sources. Include citations [1], [2]. Audience: {request.audience}"
        user_prompt = f"Query: {request.query}\n\nSources:\n{sources_text}"
        
        response = llm_client.complete(system_prompt, user_prompt)
        state.final_answer = response.content
        latency = time.time() - start_time
        
        console.print(Panel.fit(state.final_answer, title=f"Single-Agent Baseline (Latency: {latency:.2f}s, Cost: ${response.cost_usd or 0:.4f})"))
    except Exception as exc:
        console.print(Panel.fit(str(exc), title="Error", style="red"))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    state = ResearchState(request=_parse_query(query))
    workflow = MultiAgentWorkflow()
    try:
        result = workflow.run(state)
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    console.print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
