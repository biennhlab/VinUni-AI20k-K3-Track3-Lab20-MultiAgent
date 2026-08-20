"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass
from openai import OpenAI, APIConnectionError, RateLimitError, APITimeoutError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client skeleton."""

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion."""

        settings = get_settings()
        api_key = settings.nvidia_api_key
        model = settings.nvidia_model
        
        if not api_key:
            raise ValueError("NVIDIA_API_KEY is not set in environment/config.")
            
        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
        
        @retry(
            wait=wait_exponential(multiplier=1, min=2, max=10),
            stop=stop_after_attempt(3),
            retry=retry_if_exception_type((APIConnectionError, RateLimitError, APITimeoutError))
        )
        def _call_api():
            return client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=2048
            )
            
        try:
            response = _call_api()
            content = response.choices[0].message.content or ""
            usage = response.usage
            in_tokens = usage.prompt_tokens if usage else 0
            out_tokens = usage.completion_tokens if usage else 0
            
            # Rough cost estimation for llama3-70b (e.g. $0.85 per 1M in/out tokens for NIM, but we just put dummy formula)
            cost = (in_tokens + out_tokens) * 0.00000085
            
            return LLMResponse(
                content=content,
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                cost_usd=cost
            )
        except Exception as e:
            # Fallback for errors after retries
            raise RuntimeError(f"LLM completion failed: {str(e)}") from e
