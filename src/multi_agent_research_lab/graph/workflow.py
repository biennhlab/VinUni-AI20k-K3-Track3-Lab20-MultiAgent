"""LangGraph workflow skeleton."""

from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def build(self) -> object:
        from langgraph.graph import StateGraph, END
        from multi_agent_research_lab.core.schemas import AgentName
        from multi_agent_research_lab.agents.supervisor import SupervisorAgent
        from multi_agent_research_lab.agents.researcher import ResearcherAgent
        from multi_agent_research_lab.agents.analyst import AnalystAgent
        from multi_agent_research_lab.agents.writer import WriterAgent
        from multi_agent_research_lab.agents.critic import CriticAgent
        
        # We need a state dictionary for LangGraph since it passes dict state if we don't configure properly, but Pydantic v2 support exists.
        # However, to be safe, we wrap it. Actually Langgraph supports passing Pydantic models directly or dataclasses.
        graph = StateGraph(ResearchState)
        
        supervisor = SupervisorAgent()
        researcher = ResearcherAgent()
        analyst = AnalystAgent()
        writer = WriterAgent()
        critic = CriticAgent()
        
        graph.add_node(AgentName.SUPERVISOR, supervisor.run)
        graph.add_node(AgentName.RESEARCHER, researcher.run)
        graph.add_node(AgentName.ANALYST, analyst.run)
        graph.add_node(AgentName.WRITER, writer.run)
        graph.add_node(AgentName.CRITIC, critic.run)
        
        # Edge from workers to supervisor
        graph.add_edge(AgentName.RESEARCHER, AgentName.SUPERVISOR)
        graph.add_edge(AgentName.ANALYST, AgentName.SUPERVISOR)
        graph.add_edge(AgentName.WRITER, AgentName.CRITIC)
        graph.add_edge(AgentName.CRITIC, AgentName.SUPERVISOR)
        
        # Conditional edge from supervisor
        def route(state: ResearchState) -> str:
            if state.route_history:
                return state.route_history[-1]
            return END
            
        graph.add_conditional_edges(
            AgentName.SUPERVISOR,
            route,
            {
                AgentName.RESEARCHER: AgentName.RESEARCHER,
                AgentName.ANALYST: AgentName.ANALYST,
                AgentName.WRITER: AgentName.WRITER,
                "END": END
            }
        )
        
        graph.set_entry_point(AgentName.SUPERVISOR)
        
        self.app = graph.compile()
        return self.app

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        
        if not hasattr(self, "app"):
            self.build()
            
        final_state = self.app.invoke(state)
        # LangGraph invoke returns either dict or model based on setup
        if isinstance(final_state, dict):
            return ResearchState(**final_state)
        return final_state
