"""
FastAPI application for T2T chatbot.
Provides web interface and MCP endpoints using main.py's ChatbotEngine.
"""

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from main import ChatbotEngine
from data_cache import is_cache_fresh, get_cache_date

# Initialize FastAPI app
app = FastAPI(
    title="T2T Chatbot API",
    description="Web interface and MCP endpoints for T2T chatbot",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chatbot engine instance
chatbot_engine = ChatbotEngine()


# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message")
    session_id: str = Field("default", description="Session ID to maintain conversation history")


class ChatResponse(BaseModel):
    response: str = Field(..., description="Bot's response")
    session_id: str = Field(..., description="Session ID")


class KnowledgeResponse(BaseModel):
    website_data: str = Field(..., description="Cached website documentation")
    events_data: str = Field(..., description="Cached events information")
    cache_date: str = Field(..., description="Date when cache was created")
    is_fresh: bool = Field(..., description="Whether cache is from today")


@app.on_event("startup")
async def startup_event():
    """Initialize chatbot engine on startup."""
    print("Starting T2T API server...")
    try:
        chatbot_engine.initialize()
        print("T2T API server ready.")
    except Exception as e:
        print(f"Error initializing chatbot engine: {e}")
        print("Server started but chat functionality may not work.")


@app.get("/")
async def root():
    """Serve the web chat interface."""
    chat_html_path = Path(__file__).parent / "chat.html"
    if chat_html_path.exists():
        return FileResponse(chat_html_path)
    else:
        return {
            "message": "T2T Chatbot API",
            "error": "Web interface not found. Please ensure chat.html exists.",
            "endpoints": {
                "/chat": "POST - Conversational AI",
                "/knowledge": "GET - Cached knowledge data (MCP endpoint)",
                "/health": "GET - Health check"
            }
        }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint using Gemini AI.
    
    Uses the ChatbotEngine from main.py to process messages with full T2T context.
    Maintains conversation history per session.
    """
    try:
        response = chatbot_engine.chat(
            message=request.message,
            session_id=request.session_id
        )
        
        return ChatResponse(
            response=response,
            session_id=request.session_id
        )
        
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


@app.get("/knowledge", response_model=KnowledgeResponse)
async def get_knowledge():
    """
    MCP endpoint: Returns cached T2T knowledge data.
    
    Returns both website documentation and events data from t2t_knowledge.txt.
    Perfect for LLM tools that need access to T2T information.
    """
    try:
        # Get cached knowledge from engine
        website_content, events_text = chatbot_engine.get_cached_knowledge()
        
        if not website_content:
            raise HTTPException(
                status_code=503,
                detail="Knowledge cache is empty. Please run 'python main.py' to populate the cache."
            )
        
        return KnowledgeResponse(
            website_data=website_content,
            events_data=events_text,
            cache_date=get_cache_date() or "unknown",
            is_fresh=is_cache_fresh()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve knowledge: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    has_knowledge = bool(chatbot_engine.website_content)
    
    return {
        "status": "healthy" if has_knowledge else "degraded",
        "timestamp": datetime.now().isoformat(),
        "chatbot_ready": has_knowledge,
        "cache_fresh": is_cache_fresh(),
        "cache_date": get_cache_date()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
