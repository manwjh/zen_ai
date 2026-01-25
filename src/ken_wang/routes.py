"""
KenWang API 路由 (FastAPI)

对外暴露的接口：
1. POST /ken-wang/moderate - 审核内容（使用通用审核机器人）
2. POST /ken-wang/write-article - 生成文章
3. POST /ken-wang/respond-comment - 回复评论
"""

import json
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..llm import load_llm_config
from .sage import SageWriter
from .comment_handler import CommentHandler
from .config import get_zen_content_url, get_internal_api_key

# 导入通用安全审核机器人
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'zenheart_robot'))

try:
    from safety_guard_bot import ContentModerator as SafetyGuard, ContentType
    SAFETY_GUARD_AVAILABLE = True
except ImportError as e:
    logging.warning(f"安全审核机器人不可用: {e}")
    SAFETY_GUARD_AVAILABLE = False
    SafetyGuard = None

# 导入 KenWang 专用审核器（用于质量评估和撰文决策）
from .moderator import ContentModerator as KenWangModerator

logger = logging.getLogger(__name__)

# 获取配置
ZEN_CONTENT_URL = get_zen_content_url()
INTERNAL_API_KEY = get_internal_api_key()

# 创建 FastAPI Router
ken_wang_router = APIRouter(prefix="/ken-wang", tags=["ken-wang"])

# 全局组件（在生产中应该通过依赖注入）
_llm_config = None
_safety_guard = None  # 安全审核（第一层）
_ken_wang_moderator = None  # KenWang 质量评估（第二层）
_sage = None
_comment_handler = None


def _init_components():
    """初始化 KenWang 组件（两层审核架构）"""
    global _llm_config, _safety_guard, _ken_wang_moderator, _sage, _comment_handler
    
    if _llm_config is None:
        _llm_config = load_llm_config()
        
        # 第一层：安全审核机器人（快速过滤违规内容）
        if SAFETY_GUARD_AVAILABLE:
            _safety_guard = SafetyGuard(_llm_config, strategy='llm_driven')
            logger.info("✅ 安全审核机器人已加载（第一层）")
        else:
            _safety_guard = None
            logger.warning("⚠️ 安全审核机器人不可用")
        
        # 第二层：KenWang 质量评估（判断是否撰文）
        _ken_wang_moderator = KenWangModerator(_llm_config)
        logger.info("✅ KenWang 质量评估器已加载（第二层）")
        
        _sage = SageWriter(_llm_config)
        _comment_handler = CommentHandler(_llm_config)


# ========================================
# Request/Response Models
# ========================================

class ModerateRequest(BaseModel):
    """审核请求"""
    content_type: str = Field(..., description="内容类型: question/comment")
    content_id: int = Field(..., description="内容ID")


class ModerateResponse(BaseModel):
    """审核响应"""
    success: bool
    action: str = Field(..., description="审核动作: approve/reject")
    reason: str = Field(..., description="审核原因")


class WriteArticleRequest(BaseModel):
    """文章生成请求"""
    question_id: int = Field(..., description="问题ID")


class WriteArticleResponse(BaseModel):
    """文章生成响应"""
    success: bool
    article_id: Optional[int] = None
    title: str


class RespondCommentRequest(BaseModel):
    """评论回复请求"""
    comment_id: int = Field(..., description="评论ID")


class RespondCommentResponse(BaseModel):
    """评论回复响应"""
    success: bool
    responded: bool
    message: Optional[str] = None
    response: Optional[str] = None


# ========================================
# 1. 审核接口
# ========================================

@ken_wang_router.post('/moderate', response_model=ModerateResponse)
async def moderate_content(request: ModerateRequest):
    """
    两层审核架构：
    1. safety_guard_bot: 安全过滤（违规、暴力、色情）
    2. KenWang: 质量评估（是否值得撰文）
    
    支持：
    - question: 问题审核
    - comment: 评论审核
    """
    _init_components()
    
    if not _ken_wang_moderator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='审核服务不可用'
        )
    
    try:
        if request.content_type == 'question':
            # 获取问题内容
            question_data = await _get_question_from_zen_content(request.content_id)
            
            if not question_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='无法获取问题内容'
                )
            
            question = question_data['question']
            language = question_data.get('language', 'zh')
            
            # 第一层：安全审核（安检员）
            if _safety_guard:
                safety_result = _safety_guard.moderate_question(
                    question=question,
                    language=language
                )
                
                if safety_result.is_rejected:
                    # 安检员拒绝，直接结束，不经过 KenWang
                    # 构建详细的反馈信息
                    detailed_feedback = safety_result.reason
                    
                    # 添加具体的担忧点
                    if safety_result.concerns and len(safety_result.concerns) > 0:
                        concerns_text = '、'.join(safety_result.concerns)
                        detailed_feedback += f"\n\n具体问题：{concerns_text}"
                    
                    # 添加改进建议
                    if safety_result.suggestions and len(safety_result.suggestions) > 0:
                        suggestions_text = '；'.join(safety_result.suggestions)
                        detailed_feedback += f"\n\n建议：{suggestions_text}"
                    
                    result = {
                        'action': 'reject',
                        'reason': '内容安全审核未通过',
                        'ken_wang_feedback': detailed_feedback,
                        'feedback_source': 'safety_guard',  # 标注来源：安检员
                        'safety_score': safety_result.safety_score,
                        'quality_score': 0,
                        'worthy_of_article': False,
                        'estimated_length': 'short',
                        'details': {
                            'safety_guard_reason': safety_result.reason,
                            'concerns': safety_result.concerns,
                            'suggestions': safety_result.suggestions
                        }
                    }
                    
                    logger.warning(f"安检员拒绝: {safety_result.reason}")
                    await _save_moderation_result_to_zen_content(request.content_id, result)
                    
                    return ModerateResponse(
                        success=True,
                        action='reject',
                        reason=safety_result.reason
                    )
            
            # 第二层：KenWang 质量评估（判断是否值得撰文）
            result = _ken_wang_moderator.moderate_question(
                question=question,
                language=language
            )
            
            # 标注反馈来源为 KenWang
            result['feedback_source'] = 'kenwang'
            
            logger.info(
                f"KenWang 评估: action={result['action']}, "
                f"quality={result['quality_score']}, "
                f"feedback={result.get('ken_wang_feedback', 'N/A')[:50]}"
            )
            
            # 回传审核结果到zen_content
            await _save_moderation_result_to_zen_content(request.content_id, result)
            
            return ModerateResponse(
                success=True,
                action=result['action'],
                reason=result.get('ken_wang_feedback') or result['reason']
            )
            
        elif request.content_type == 'comment':
            # 获取评论内容
            comment_data = await _get_comment_from_zen_content(request.content_id)
            
            if not comment_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='无法获取评论内容'
                )
            
            # 🤖 使用通用审核机器人（LLM 驱动）
            result = _moderator.moderate_comment(
                comment=comment_data['content'],
                language=comment_data.get('language', 'zh')
            )
            
            logger.info(
                f"评论审核 [LLM驱动]: action={result.action}, "
                f"safety={result.safety_score}, "
                f"quality={result.quality_score}"
            )
            
            # 转换为字典格式
            result_dict = {
                'action': result.action,
                'reason': result.reason,
                'safety_score': result.safety_score,
                'should_ken_respond': result.should_respond
            }
            
            # 回传审核结果到zen_content
            await _save_comment_moderation_result(request.content_id, result_dict)
            
            return ModerateResponse(
                success=True,
                action=result.action,
                reason=result.reason
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='不支持的内容类型'
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"审核失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========================================
# 2. 文章生成接口
# ========================================

@ken_wang_router.post('/write-article', response_model=WriteArticleResponse)
async def write_article(request: WriteArticleRequest):
    """生成文章"""
    _init_components()
    
    try:
        # 获取问题内容
        question_data = await _get_question_from_zen_content(request.question_id)
        
        if not question_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='无法获取问题内容'
            )
        
        # 生成文章
        article = _sage.write_article(
            question=question_data['question'],
            estimated_length=question_data.get('estimated_length', 'medium'),
            language=question_data.get('language', 'zh')
        )
        
        # 保存文章到zen_content
        article['question_id'] = request.question_id
        article['language'] = question_data.get('language', 'zh')
        
        # tags 和 metadata 已经是对象，直接传递
        await _save_article_to_zen_content(article)
        
        return WriteArticleResponse(
            success=True,
            article_id=article.get('article_id'),
            title=article['title']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文章生成失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========================================
# 3. 评论回复接口
# ========================================

@ken_wang_router.post('/respond-comment', response_model=RespondCommentResponse)
async def respond_comment(request: RespondCommentRequest):
    """回复评论"""
    _init_components()
    
    try:
        # 获取评论内容和文章信息
        comment_data = await _get_comment_from_zen_content(request.comment_id)
        
        if not comment_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='无法获取评论内容'
            )
        
        # 判断是否回复
        should_respond = _comment_handler.should_respond(
            comment=comment_data['content'],
            article_title=comment_data['article_title'],
            is_mentioned=comment_data.get('mentioned_ken', False),
            language=comment_data.get('language', 'zh')
        )
        
        if not should_respond:
            return RespondCommentResponse(
                success=True,
                responded=False,
                message='KenWang选择不回复此评论'
            )
        
        # 生成回复（传递评论线索）
        response_data = _comment_handler.generate_response(
            comment=comment_data['content'],
            article_title=comment_data['article_title'],
            article_summary=comment_data.get('article_summary', ''),
            thread=comment_data.get('thread', []),  # 传递N级跟帖上下文
            is_mentioned=comment_data.get('mentioned_ken', False),
            language=comment_data.get('language', 'zh')
        )
        
        if not response_data:
            return RespondCommentResponse(
                success=True,
                responded=False,
                message='KenWang决定不回复'
            )
        
        # 记录评论线索深度
        thread_depth = comment_data.get('thread_depth', 0)
        logger.info(f"KenWang回复评论 (评论线索深度={thread_depth})")
        
        # 保存回复到zen_content
        await _save_comment_response_to_zen_content(
            comment_id=request.comment_id,
            response=response_data['response'],
            tone=response_data['tone']
        )
        
        return RespondCommentResponse(
            success=True,
            responded=True,
            response=response_data['response']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"评论回复失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========================================
# 辅助函数：与zen_content通信 (异步版本)
# ========================================

async def _get_question_from_zen_content(question_id: int) -> Optional[Dict[str, Any]]:
    """从zen_content获取问题内容"""
    try:
        url = f"{ZEN_CONTENT_URL}/mirror/internal/questions/{question_id}"
        logger.info(f"[DEBUG] 正在请求: {url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
        
        logger.info(f"[DEBUG] 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"[DEBUG] 获取到问题: {data.get('question', '')[:50]}...")
            return data
        else:
            logger.error(f"获取问题失败: {response.status_code}, 响应: {response.text[:200]}")
            return None
            
    except Exception as e:
        logger.error(f"获取问题异常: {e}", exc_info=True)
        return None


async def _save_moderation_result_to_zen_content(question_id: int, result: dict):
    """将审核结果保存到zen_content"""
    try:
        url = f"{ZEN_CONTENT_URL}/mirror/internal/moderation/result"
        
        # 准备详细信息，包含反馈来源
        details = result.get('details', {})
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except:
                details = {}
        details['feedback_source'] = result.get('feedback_source', 'kenwang')
        
        payload = {
            'question_id': question_id,
            'action': result['action'],
            'reason': result['reason'],
            'ken_wang_feedback': result.get('ken_wang_feedback', ''),  # KenWang的个性化反馈
            'safety_score': result['safety_score'],
            'quality_score': result['quality_score'],
            'worthy_of_article': result.get('worthy_of_article', False),
            'estimated_length': result.get('estimated_length', 'medium'),
            'details': details
        }
        
        # 添加API密钥头
        headers = {
            'X-API-Key': INTERNAL_API_KEY
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
        
        if response.status_code == 200:
            logger.info(f"审核结果已保存: question_id={question_id}, ken_wang_feedback={result.get('ken_wang_feedback', 'N/A')[:50]}")
        else:
            logger.error(f"保存审核结果失败: {response.status_code}")
            
    except Exception as e:
        logger.error(f"保存审核结果异常: {e}")


async def _save_article_to_zen_content(article: dict):
    """将文章保存到zen_content"""
    try:
        url = f"{ZEN_CONTENT_URL}/mirror/internal/articles"
        
        logger.info(f"[DEBUG] 准备保存文章: {article.keys()}")
        logger.info(f"[DEBUG] tags类型: {type(article.get('tags'))}, metadata类型: {type(article.get('metadata'))}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=article, timeout=30.0)
        
        if response.status_code == 200:
            result = response.json()
            article['article_id'] = result.get('article_id')
            logger.info(f"文章已保存: article_id={article.get('article_id')}")
        else:
            logger.error(f"保存文章失败: {response.status_code}, 响应: {response.text[:500]}")
            
    except Exception as e:
        logger.error(f"保存文章异常: {e}", exc_info=True)


async def _get_comment_from_zen_content(comment_id: int) -> Optional[Dict[str, Any]]:
    """从zen_content获取评论内容"""
    try:
        url = f"{ZEN_CONTENT_URL}/mirror/internal/comments/{comment_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"获取评论失败: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"获取评论异常: {e}")
        return None


async def _save_comment_moderation_result(comment_id: int, result: dict):
    """将评论审核结果保存到zen_content"""
    try:
        url = f"{ZEN_CONTENT_URL}/mirror/internal/comments/{comment_id}/moderation"
        
        payload = {
            'comment_id': comment_id,
            'action': result['action'],
            'reason': result['reason'],
            'safety_score': result['safety_score'],
            'should_ken_respond': result.get('should_ken_respond', False)
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
        
        if response.status_code == 200:
            logger.info(f"评论审核结果已保存: comment_id={comment_id}")
        else:
            logger.error(f"保存评论审核结果失败: {response.status_code}")
            
    except Exception as e:
        logger.error(f"保存评论审核结果异常: {e}")


async def _save_comment_response_to_zen_content(comment_id: int, response: str, tone: str):
    """将KenWang的回复保存为新评论"""
    try:
        url = f"{ZEN_CONTENT_URL}/mirror/internal/comments/ken-response"
        
        payload = {
            'parent_comment_id': comment_id,
            'response': response,
            'tone': tone
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10.0)
        
        if resp.status_code == 200:
            logger.info(f"KenWang回复已保存: parent_id={comment_id}")
        else:
            logger.error(f"保存回复失败: {resp.status_code}")
            
    except Exception as e:
        logger.error(f"保存回复异常: {e}")
