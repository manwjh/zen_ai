from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..core.models import PromptPolicy
from ..core.prompt import render_prompt
from ..llm import load_llm_config
from ..orator import ZenAiOrator
from ..storage import ResonanceArchive
from ..trainer import ZenAiTrainer


# ========================================
# Request/Response Models
# ========================================

class ChatRequest(BaseModel):
    """User chat input"""
    user_input: str = Field(..., min_length=1, max_length=10000)
    metadata: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    """Orator response"""
    interaction_id: int
    response_text: str
    refusal: bool
    prompt_version: int
    timestamp: datetime


class FeedbackRequest(BaseModel):
    """User feedback submission"""
    interaction_id: int
    feedback: str = Field(..., min_length=1, max_length=500)


class FeedbackResponse(BaseModel):
    """Feedback confirmation"""
    interaction_id: int
    feedback: str
    recorded_at: datetime


class StatusResponse(BaseModel):
    """System status"""
    prompt_version: int
    current_iteration_id: int | None
    frozen: bool
    killed: bool
    policy: dict[str, Any]
    total_interactions: int
    total_iterations: int


class MetricsResponse(BaseModel):
    """Current metrics summary"""
    iteration_id: int | None
    total_interactions: int
    metrics: dict[str, float | int] | None


# ========================================
# Application State
# ========================================

class AppState:
    """Global application state"""
    archive: ResonanceArchive | None = None
    trainer: ZenAiTrainer | None = None
    orator: ZenAiOrator | None = None


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize and cleanup application resources.
    
    Initialization order:
    1. Load configuration
    2. Initialize Archive (storage layer)
    3. Initialize first prompt if needed
    4. Initialize Trainer (修炼者) - silent practice
    5. Initialize Orator (布道者) - verbal teaching
    
    Both Trainer and Orator are core components, equally initialized.
    修炼者和布道者都是核心组件，平等初始化。
    """
    # Load configuration
    from ..config import load_config
    config = load_config()
    
    print("\n" + "="*60)
    print("ZenAi System Initialization / ZenAi 系统初始化")
    print("="*60)
    
    # 1. Initialize Archive (storage layer)
    db_path = config.paths.get_database_path()
    archive = ResonanceArchive(db_path=db_path)
    print(f"✓ Archive initialized: {db_path}")
    
    # 2. Initialize first prompt if needed
    latest_prompt = archive.get_latest_prompt()
    if not latest_prompt:
        default_policy = PromptPolicy(
            max_output_tokens=config.initial_policy.max_output_tokens,
            refusal_threshold=config.initial_policy.refusal_threshold,
            perturbation_level=config.initial_policy.perturbation_level,
            temperature=config.initial_policy.temperature,
        )
        prompt_text = render_prompt(default_policy)
        archive.save_prompt(
            version=1,
            prompt_text=prompt_text,
            policy=default_policy.to_dict(),
        )
        print(f"✓ Initial prompt (v1) created")
    else:
        print(f"✓ Existing prompt loaded (v{latest_prompt.version})")
    
    # 3. Initialize Trainer (修炼者)
    trainer = ZenAiTrainer.from_config(archive, config)
    print(f"✓ Trainer (修炼者) initialized - silent practice through computation")
    
    # 4. Initialize Orator (布道者)
    llm_config = load_llm_config()
    orator = ZenAiOrator(
        llm_config=llm_config,
        archive=archive,
    )
    print(f"✓ Orator (布道者) initialized - verbal teaching through LLM")
    
    # Store in app state
    app_state.archive = archive
    app_state.trainer = trainer
    app_state.orator = orator
    
    print("="*60)
    print("System ready / 系统就绪")
    print("="*60 + "\n")
    
    yield
    
    # Cleanup (if needed)
    print("\nShutting down ZenAi system...")
    pass


# ========================================
# FastAPI Application
# ========================================

app = FastAPI(
    title="ZenAi API",
    description="ZenAi Public Practice System API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# API Endpoints
# ========================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "ZenAi Orator API",
        "version": "0.1.0",
        "status": "operational",
    }


@app.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest):
    """
    Send message to ZenAi Orator and receive response.
    
    This is the main interaction endpoint where users communicate
    with the ZenAi system.
    """
    if not app_state.orator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orator not initialized",
        )
    
    # Check if system is killed
    if app_state.archive and app_state.archive.is_killed():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System has been terminated",
        )
    
    try:
        response = app_state.orator.respond(
            user_input=request.user_input,
            metadata=request.metadata,
        )
        return ChatResponse(
            interaction_id=response.interaction_id,
            response_text=response.response_text,
            refusal=response.refusal,
            prompt_version=response.prompt_version,
            timestamp=response.timestamp,
        )
    except Exception as exc:
        # Log full error internally but return generic message to user
        # to avoid exposing sensitive configuration details
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing request",
        )


@app.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_200_OK)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback for an interaction.
    
    Feedback helps the system understand which responses
    resonated with users and which were rejected.
    """
    if not app_state.orator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orator not initialized",
        )
    
    try:
        app_state.orator.record_feedback(
            interaction_id=request.interaction_id,
            feedback=request.feedback,
        )
        return FeedbackResponse(
            interaction_id=request.interaction_id,
            feedback=request.feedback,
            recorded_at=datetime.utcnow(),
        )
    except Exception as exc:
        # Log full error internally but return generic message to user
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while recording feedback",
        )


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get current system status.
    
    Returns information about the current prompt version,
    system state, and whether evolution is frozen or killed.
    """
    if not app_state.orator or not app_state.archive:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not initialized",
        )
    
    status_info = app_state.orator.get_system_status()
    total_interactions = app_state.archive.get_interaction_count()
    total_iterations = app_state.archive.get_iteration_count()
    
    return StatusResponse(
        prompt_version=status_info["prompt_version"],
        current_iteration_id=status_info["current_iteration_id"],
        frozen=status_info["frozen"],
        killed=status_info["killed"],
        policy=status_info["policy"],
        total_interactions=total_interactions,
        total_iterations=total_iterations,
    )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get current iteration metrics.
    
    Returns metrics for the most recent completed iteration.
    """
    if not app_state.archive:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Archive not initialized",
        )
    
    latest_iteration = app_state.archive.get_latest_iteration()
    if not latest_iteration:
        return MetricsResponse(
            iteration_id=None,
            total_interactions=0,
            metrics=None,
        )
    
    return MetricsResponse(
        iteration_id=latest_iteration.id,
        total_interactions=latest_iteration.total_interactions,
        metrics=latest_iteration.metrics,
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }
