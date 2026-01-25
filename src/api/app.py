from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, List, Union

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .. import __version__
from ..core.models import PromptPolicy
from ..core.prompt import render_prompt
from ..llm import load_llm_config
from ..orator import ZenAiOrator
from ..storage import ResonanceArchive
from ..trainer import ZenAiTrainer
from ..llm import send_chat_completion, LlmMessage
from ..ken_wang.routes import ken_wang_router


# ========================================
# Request/Response Models
# ========================================

class ChatRequest(BaseModel):
    """User chat input"""
    user_input: str = Field(..., min_length=1, max_length=10000)
    metadata: Optional[Dict[str, Any]] = None
    language: str = Field(default='en', pattern='^(zh|zh-tw|en|ja|ko)$')


class ChatResponse(BaseModel):
    """Orator response"""
    interaction_id: int
    response_text: str
    refusal: bool
    prompt_version: int
    timestamp: datetime


class FeedbackRequest(BaseModel):
    """User feedback submission - behavior-based"""
    interaction_id: int
    behavior: str = Field(..., description="User behavior: agree/download/explain/comment/timeout")
    comment: str = Field(default="", max_length=500, description="User comment (optional)")
    timestamp: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Feedback confirmation"""
    interaction_id: int
    behavior: str
    feedback_type: str = Field(description="Mapped feedback type: resonance/rejection/ignore")
    recorded_at: datetime


class StatusResponse(BaseModel):
    """System status"""
    system_version: str
    prompt_version: int
    current_iteration_id: Optional[int]
    frozen: bool
    killed: bool
    policy: Dict[str, Any]
    total_interactions: int
    total_iterations: int


class MetricsResponse(BaseModel):
    """Current metrics summary"""
    iteration_id: Optional[int]
    total_interactions: int
    metrics: Optional[Dict[str, Union[float, int]]]


class GathaResponse(BaseModel):
    """Single gatha (Buddhist verse) with explanation"""
    iteration_id: int
    end_time: Optional[str]
    state: str
    metrics: Dict[str, Any]
    # Gatha data fields
    gatha: str
    explanation: Optional[str] = None
    questions_count: int
    generation_time: Optional[float] = None
    resonance_ratio: Optional[float] = None
    # TTS fields (future)
    audio_generated: bool = False
    audio_path: Optional[str] = None
    audio_duration: Optional[float] = None


class GathasResponse(BaseModel):
    """Collection of gathas"""
    gathas: List[GathaResponse]
    count: int


class ExplainRequest(BaseModel):
    """Request for explaining a Zen answer"""
    question: str = Field(..., min_length=1, max_length=10000)
    zen_answer: str = Field(..., min_length=1, max_length=10000)
    language: str = Field(default='en', pattern='^(zh|zh-tw|en|ja|ko)$')


class ExplainResponse(BaseModel):
    """Plain language explanation of Zen answer"""
    explanation: str
    timestamp: datetime


class GenerateRequest(BaseModel):
    """Generic LLM generation request"""
    prompt: str = Field(..., min_length=1, max_length=50000, description="The prompt to send to LLM")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=1000, ge=1, le=4000, description="Maximum tokens to generate")


class GenerateResponse(BaseModel):
    """Generic LLM generation response"""
    text: str = Field(description="Generated text from LLM")
    timestamp: datetime


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
    version=__version__,
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

# Include routers
app.include_router(ken_wang_router)


# ========================================
# API Endpoints
# ========================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "ZenAi Orator API",
        "version": __version__,
        "status": "operational",
        "documentation": "/docs",
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
            language=request.language,
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


"""
用户行为到反馈类型的映射规则
集中管理，便于调整和扩展
"""
BEHAVIOR_FEEDBACK_MAPPING = {
    # 🟢 正面反馈 - Resonance
    'agree': {
        'feedback_type': 'resonance',
        'weight': 1.0,
        'description': '用户主动表示受到启发',
    },
    'download': {
        'feedback_type': 'resonance',
        'weight': 0.8,
        'description': '用户认为对话有保存价值',
    },
    
    # 🔴 负面反馈 - Rejection
    'explain': {
        'feedback_type': 'rejection',
        'weight': 0.6,
        'description': '用户对回答感到困惑，需要更简单的表达',
    },
    
    # 🟡 中性反馈 - Ignore
    'comment': {
        'feedback_type': 'ignore',  # 默认中性，可通过情感分析调整
        'weight': 0.0,
        'description': '普通交流评论，可做进一步情感分析',
    },
    'timeout': {
        'feedback_type': 'ignore',
        'weight': 0.0,
        'description': '用户阅读后未采取行动',
    }
}


@app.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_200_OK)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback based on behavior (静默反馈映射)
    
    前端发送原始用户行为，后端负责映射到标准的 feedback_type。
    同时保存用户的评论内容到 extra_data，不会丢失信息。
    
    映射逻辑：
    - agree (启发) → resonance
    - download (下载) → resonance
    - explain (请求解释) → rejection
    - comment (评论) → ignore (可通过情感分析调整)
    - timeout (无操作) → ignore
    """
    if not app_state.archive:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Archive not initialized",
        )
    
    try:
        # 1. 获取映射规则
        mapping = BEHAVIOR_FEEDBACK_MAPPING.get(request.behavior)
        
        if not mapping:
            print(f"[Feedback] ⚠️  Unknown behavior: {request.behavior}, defaulting to 'ignore'")
            feedback_type = 'ignore'
            description = f"Unknown behavior: {request.behavior}"
        else:
            feedback_type = mapping['feedback_type']
            description = mapping['description']
        
        # 2. 可选：对评论内容做情感分析（未来扩展）
        # if request.behavior == 'comment' and request.comment:
        #     sentiment_score = analyze_sentiment(request.comment)
        #     if sentiment_score > 0.7:
        #         feedback_type = 'resonance'
        #     elif sentiment_score < 0.3:
        #         feedback_type = 'rejection'
        
        # 3. 构建要保存的详细数据
        feedback_data = {
            'behavior': request.behavior,
            'feedback_type': feedback_type,
            'timestamp': request.timestamp or datetime.utcnow().isoformat(),
        }
        
        # 如果有评论内容，保存到 extra_data
        if request.comment:
            feedback_data['comment'] = request.comment
            feedback_data['comment_length'] = len(request.comment)
        
        # 4. 更新数据库：feedback字段存类型，extra_data存详细信息
        app_state.archive.update_interaction_feedback(
            interaction_id=request.interaction_id,
            feedback=feedback_type,  # 标准类型
            feedback_data=feedback_data,  # 详细数据
        )
        
        # 5. 日志记录
        log_msg = (
            f"[Feedback] ✓ Recorded: ID={request.interaction_id}, "
            f"Behavior={request.behavior} → Type={feedback_type}"
        )
        if request.comment:
            log_msg += f", Comment='{request.comment[:50]}...'"
        print(log_msg)
        print(f"[Feedback]    Reason: {description}")
        
        # 6. 返回响应
        return FeedbackResponse(
            interaction_id=request.interaction_id,
            behavior=request.behavior,
            feedback_type=feedback_type,
            recorded_at=datetime.utcnow(),
        )
        
    except Exception as exc:
        print(f"[Feedback] ❌ Error: {exc}")
        import traceback
        traceback.print_exc()
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
        system_version=__version__,
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


@app.get("/gathas", response_model=GathasResponse)
async def get_recent_gathas(limit: int = 10):
    """
    Get recent gathas (Buddhist verses) with explanations.
    
    Gathas are poetic reflections generated by the Trainer after each iteration,
    capturing the essence of user questions from that practice period.
    Each gatha includes a plain language explanation suitable for TTS audio generation.
    
    Args:
        limit: Maximum number of gathas to return (default: 10)
    
    Returns:
        Collection of recent gathas with complete data
    """
    if not app_state.archive:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Archive not initialized",
        )
    
    gathas_data = app_state.archive.get_all_gathas(limit=limit)
    
    gathas = [
        GathaResponse(
            iteration_id=g["iteration_id"],
            end_time=g.get("end_time"),
            state=g["state"],
            metrics=g["metrics"],
            gatha=g.get("gatha", ""),
            explanation=g.get("explanation"),
            questions_count=g.get("questions_count", 0),
            generation_time=g.get("generation_time"),
            resonance_ratio=g.get("resonance_ratio"),
            audio_generated=g.get("audio_generated", False),
            audio_path=g.get("audio_path"),
            audio_duration=g.get("audio_duration"),
        )
        for g in gathas_data
    ]
    
    return GathasResponse(gathas=gathas, count=len(gathas))


@app.get("/gathas/{iteration_id}")
async def get_gatha_by_iteration(iteration_id: int):
    """
    Get complete gatha data for a specific iteration.
    
    Args:
        iteration_id: Iteration ID
        
    Returns:
        Complete gatha data including text, explanation, and metadata
    """
    if not app_state.archive:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Archive not initialized",
        )
    
    gatha_data = app_state.archive.get_gatha(iteration_id)
    
    if not gatha_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No gatha found for iteration {iteration_id}",
        )
    
    # Get iteration info
    iteration = app_state.archive.get_iteration(iteration_id)
    if not iteration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Iteration {iteration_id} not found",
        )
    
    return {
        "iteration_id": iteration_id,
        "end_time": iteration.end_time.isoformat() if iteration.end_time else None,
        "state": iteration.state,
        "metrics": iteration.metrics,
        **gatha_data,  # Include all gatha data
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": __version__,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_200_OK)
async def generate(request: GenerateRequest):
    """
    Generic LLM generation endpoint.
    
    This endpoint provides direct access to the underlying LLM without
    ZenAI's prompt wrapping. Useful for custom applications like the
    Symbol Alchemy game.
    
    Args:
        prompt: The prompt to send to LLM
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum tokens to generate (1-4000)
    
    Returns:
        Generated text from LLM
    """
    from ..llm import load_llm_config
    
    try:
        # Load LLM configuration
        llm_config = load_llm_config()
        
        # Build message
        messages = [
            LlmMessage(role="user", content=request.prompt)
        ]
        
        # Call LLM
        response_text = send_chat_completion(
            config=llm_config,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        return GenerateResponse(
            text=response_text,
            timestamp=datetime.utcnow(),
        )
        
    except Exception as exc:
        # Log error
        print(f"[LLM Generate] Error: {exc}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM generation failed: {str(exc)}",
        )


@app.post("/explain", response_model=ExplainResponse, status_code=status.HTTP_200_OK)
async def explain_zen_answer(request: ExplainRequest):
    """
    Get a plain language explanation of a Zen answer.
    
    This endpoint takes a question and its Zen answer, and returns
    a simple, easy-to-understand explanation of what the Zen answer means.
    
    Supports multiple languages: zh, zh-tw, en, ja, ko
    """
    if not app_state.orator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orator not initialized",
        )
    
    try:
        explanation = app_state.orator.explain_zen_answer(
            question=request.question,
            zen_answer=request.zen_answer,
            language=request.language,
        )
        return ExplainResponse(
            explanation=explanation,
            timestamp=datetime.utcnow(),
        )
    except Exception as exc:
        # Log full error internally but return generic message to user
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while generating explanation",
        )
