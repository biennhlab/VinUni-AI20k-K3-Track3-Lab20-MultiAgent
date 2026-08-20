"""Optional critic agent skeleton for bonus work."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        from multi_agent_research_lab.services.llm_client import LLMClient
        from multi_agent_research_lab.core.schemas import AgentResult
        
        if not state.final_answer:
            return state
            
        llm_client = LLMClient()
        
        system_prompt = "You are a Critic Agent. Check if the provided final answer contains citations like [1], [2]. Also evaluate if it hallucinates beyond the notes. Output 'PASS' if it is good, or 'FAIL: <reason>' if not."
        user_prompt = f"Final Answer:\n{state.final_answer}\n\nAnalysis Notes:\n{state.analysis_notes}\n\nReview the answer."
        
        llm_response = llm_client.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        
        if "FAIL" in llm_response.content:
            state.errors.append(llm_response.content)
            
        state.agent_results.append(AgentResult(
            agent=self.name,
            content=llm_response.content,
            metadata={"cost_usd": llm_response.cost_usd, "input_tokens": llm_response.input_tokens, "output_tokens": llm_response.output_tokens}
        ))
        
        return state
