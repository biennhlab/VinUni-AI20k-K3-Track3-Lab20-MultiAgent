import os
import json
import asyncio
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.core.schemas import ResearchQuery

app = FastAPI(title="Multi-Agent Research Lab API")

# Setup directories
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure directories exist
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# Mount static and templates
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

class ChatRequest(BaseModel):
    query: str
    max_sources: int = 5

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            workflow = MultiAgentWorkflow()
            graph_app = workflow.build()
            
            state = ResearchState(
                request=ResearchQuery(
                    query=request.query, 
                    max_sources=request.max_sources
                )
            )
            
            yield f"data: {json.dumps({'agent': 'User', 'status': 'Submitted', 'query': request.query})}\n\n"
            
            final_state = None
            
            # Using astream to avoid blocking event loop
            async for event in graph_app.astream(state):
                for node_name, state_update in event.items():
                    final_state = state_update
                    data = {
                        "agent": node_name,
                        "status": "Completed"
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    await asyncio.sleep(0.05)
            
            # Extract final answer
            final_answer = "No answer generated."
            if final_state:
                if isinstance(final_state, dict):
                    final_answer = final_state.get("final_answer", final_answer)
                else:
                    final_answer = getattr(final_state, "final_answer", final_answer)
            
            if not final_answer:
                final_answer = "Agents completed but no final answer was produced."
                
            yield f"data: {json.dumps({'type': 'final_answer', 'content': final_answer})}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
        yield "data: [DONE]\n\n"
        
    return StreamingResponse(event_stream(), media_type="text/event-stream")
