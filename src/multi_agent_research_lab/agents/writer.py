"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def run(self, state: ResearchState) -> ResearchState:
        from multi_agent_research_lab.services.llm_client import LLMClient
        from multi_agent_research_lab.core.schemas import AgentResult
        
        llm_client = LLMClient()
        
        sources_text = "\n".join([f"[{i+1}] {s.title} - {s.url}" for i, s in enumerate(state.sources)])
        
        system_prompt = f"You are a Writer Agent. Your job is to synthesize a final answer based on the analysis notes. You must include citations using [1], [2] format corresponding to the sources. Audience: {state.request.audience}"
        user_prompt = f"Query: {state.request.query}\n\nSources available:\n{sources_text}\n\nAnalysis Notes:\n{state.analysis_notes}\n\nWrite the final answer."
        
        llm_response = llm_client.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        state.final_answer = llm_response.content
        
        state.agent_results.append(AgentResult(
            agent=self.name,
            content=llm_response.content,
            metadata={"cost_usd": llm_response.cost_usd, "input_tokens": llm_response.input_tokens, "output_tokens": llm_response.output_tokens}
        ))
        
        return state
