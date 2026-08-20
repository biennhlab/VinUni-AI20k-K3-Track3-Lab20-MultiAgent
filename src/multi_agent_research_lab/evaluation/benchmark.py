"""Benchmark skeleton for single-agent vs multi-agent."""

from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency and return a placeholder metric object.

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    
    cost_usd = 0.0
    for res in state.agent_results:
        cost_usd += res.metadata.get("cost_usd", 0.0)
        
    citation_coverage = 0.0
    if state.sources and state.final_answer:
        cited_count = 0
        for i in range(len(state.sources)):
            if f"[{i+1}]" in state.final_answer:
                cited_count += 1
        citation_coverage = cited_count / len(state.sources)
        
    metrics = BenchmarkMetrics(
        run_name=run_name, 
        latency_seconds=latency,
        estimated_cost_usd=cost_usd,
        citation_coverage=citation_coverage,
        failure_rate=1.0 if state.errors else 0.0
    )
    return state, metrics
