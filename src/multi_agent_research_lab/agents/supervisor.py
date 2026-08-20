"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""

        from multi_agent_research_lab.core.config import get_settings
        from multi_agent_research_lab.core.schemas import AgentName
        
        settings = get_settings()
        
        if state.iteration >= settings.max_iterations:
            if not state.final_answer:
                state.record_route(AgentName.WRITER)
            else:
                state.record_route("END")
            return state
            
        if not state.sources:
            state.record_route(AgentName.RESEARCHER)
        elif not state.analysis_notes:
            state.record_route(AgentName.ANALYST)
        elif not state.final_answer:
            state.record_route(AgentName.WRITER)
        else:
            state.record_route("END")
            
        return state
