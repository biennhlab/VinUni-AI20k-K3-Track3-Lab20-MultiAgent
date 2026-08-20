"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def run(self, state: ResearchState) -> ResearchState:
        from multi_agent_research_lab.services.search_client import SearchClient
        from multi_agent_research_lab.services.llm_client import LLMClient
        from multi_agent_research_lab.core.schemas import AgentResult
        import json
        
        search_client = SearchClient()
        llm_client = LLMClient()
        
        # 1. Search for sources
        query = state.request.query
        max_sources = state.request.max_sources
        sources = search_client.search(query=query, max_results=max_sources)
        state.sources = sources
        
        # 2. Synthesize research notes
        sources_text = "\n\n".join([f"Source {i+1}:\nTitle: {s.title}\nURL: {s.url}\nSnippet: {s.snippet}" for i, s in enumerate(sources)])
        
        system_prompt = "You are a Research Agent. Your job is to read the raw search results and write a concise set of research notes. Extract only the facts that are relevant to the user's query."
        user_prompt = f"Query: {query}\n\nSearch Results:\n{sources_text}\n\nPlease provide concise research notes."
        
        llm_response = llm_client.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        state.research_notes = llm_response.content
        
        # 3. Add to agent results
        state.agent_results.append(AgentResult(
            agent=self.name,
            content=llm_response.content,
            metadata={"cost_usd": llm_response.cost_usd, "input_tokens": llm_response.input_tokens, "output_tokens": llm_response.output_tokens}
        ))
        
        return state
