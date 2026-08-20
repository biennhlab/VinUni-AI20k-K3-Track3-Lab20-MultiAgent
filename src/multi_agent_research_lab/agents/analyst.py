"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def run(self, state: ResearchState) -> ResearchState:
        from multi_agent_research_lab.services.llm_client import LLMClient
        from multi_agent_research_lab.core.schemas import AgentResult
        
        llm_client = LLMClient()
        
        system_prompt = "You are an Analyst Agent. Your job is to extract key claims, compare viewpoints, and flag weak evidence from the provided research notes."
        user_prompt = f"Query: {state.request.query}\n\nResearch Notes:\n{state.research_notes}\n\nPlease provide structured analysis notes."
        
        llm_response = llm_client.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        state.analysis_notes = llm_response.content
        
        state.agent_results.append(AgentResult(
            agent=self.name,
            content=llm_response.content,
            metadata={"cost_usd": llm_response.cost_usd, "input_tokens": llm_response.input_tokens, "output_tokens": llm_response.output_tokens}
        ))
        
        return state
