"""
KenWang 内容审核器

职责：
1. 审核用户提问的安全性和质量
2. 判断问题是否值得撰文
3. 评估所需文章长度
4. 验证内容语言与声明语言是否匹配
"""

import json
import logging
from typing import Dict, Any, Tuple
from ..llm import LlmMessage, send_chat_completion, LLMConfig
from .identity import get_identity_for_moderation

logger = logging.getLogger(__name__)


class ContentModerator:
    """内容审核器"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
    
    def moderate_question(self, question: str, language: str = 'zh') -> Dict[str, Any]:
        """
        审核问题
        
        返回格式：
        {
            'action': 'approve' | 'reject',
            'reason': str,
            'safety_score': int (1-10),
            'quality_score': int (1-10),
            'worthy_of_article': bool,
            'estimated_length': 'short' | 'medium' | 'long',
            'details': {...}
        }
        """
        try:
            # 构建提示词
            system_prompt = get_identity_for_moderation(language)
            
            user_prompt = f"""请审核以下问题：

问题：{question}

请按照以下JSON格式返回审核结果：
{{
    "action": "approve 或 reject",
    "reason": "简短说明（内部用）",
    "ken_wang_feedback": "给提问者的话（用我KenWang的口吻，如果拒绝的话）",
    "safety_score": 1-10,
    "quality_score": 1-10,
    "worthy_of_article": true或false,
    "estimated_length": "short, medium 或 long",
    "concerns": ["担忧点1", "担忧点2"],
    "suggestions": ["建议1", "建议2"]
}}

评分标准：
- safety_score: 10=完全安全, 1=严重违规
- quality_score: 10=极有深度, 1=毫无意义
- worthy_of_article: 是否值得KenWang撰写长文

通过标准：
- safety_score >= 7
- quality_score >= 5
- 问题有一定深度或普遍性

拒绝原因（满足任一即拒绝）：
- 违法违规、色情暴力、人身攻击
- 完全无意义的废话
- 纯粹的技术问题（不适合禅宗视角）
- 过于私人琐碎的问题

重要：ken_wang_feedback字段
- 如果通过审核：可以留空或简短鼓励（例如："好问题，让我想想怎么回答。"）
- 如果拒绝审核：必须用我KenWang的口吻给出反馈
  * 对功利问题：简短而直接，如"成功要是有快速通道，大家都去排队了。下一位。"
  * 对抬杠问题：不屑一顾，如"来抬杠的？不陪。"
  * 对废话问题：简洁打发，如"这个问题...不回答。"
  * 对质量不够的问题：温和但坚定，如"这个问题太宽泛了。想清楚具体困惑是什么，再来找我。"
  * 对不安全内容：严肃拒绝，如"这里不讨论这个。"
  
记住：
- 用第一人称"我"
- 简短有力，不超过50字
- 体现我的个性：有智慧但不装，会嗤笑无聊问题
- 参考我的案例和一致性锚点中的风格

注意：
- 不要过于苛刻，允许提问者表达困惑
- 对于真诚的提问，即使表达不完美也应通过
- KenWang的职责是"为众生解惑"，不是"拒人于千里之外"
"""
            
            # 调用LLM
            messages = [
                LlmMessage(role="system", content=system_prompt),
                LlmMessage(role="user", content=user_prompt)
            ]
            response = send_chat_completion(
                config=self.llm_config,
                messages=messages,
                temperature=0.3,  # 审核需要稳定性
                max_tokens=500
            )
            
            # 解析响应
            result = self._parse_moderation_result(response)
            
            logger.info(f"审核完成: action={result['action']}, "
                       f"safety={result['safety_score']}, "
                       f"quality={result['quality_score']}")
            
            return result
            
        except Exception as e:
            logger.error(f"审核失败: {e}")
            # 失败时默认拒绝
            return {
                'action': 'reject',
                'reason': '审核系统异常',
                'ken_wang_feedback': '系统有点忙，稍后再试吧。',
                'safety_score': 0,
                'quality_score': 0,
                'worthy_of_article': False,
                'estimated_length': 'short',
                'details': {'error': str(e)}
            }
    
    def moderate_comment(self, comment: str, language: str = 'zh') -> Dict[str, Any]:
        """
        审核评论
        
        返回格式：
        {
            'action': 'approve' | 'reject',
            'reason': str,
            'safety_score': int,
            'should_ken_respond': bool  # 是否值得KenWang回复
        }
        """
        try:
            system_prompt = get_identity_for_moderation(language)
            
            user_prompt = f"""请审核以下评论：

评论：{comment}

请按照以下JSON格式返回审核结果：
{{
    "action": "approve 或 reject",
    "reason": "简短说明",
    "safety_score": 1-10,
    "should_ken_respond": true或false
}}

通过标准：
- safety_score >= 6
- 不违反基本礼仪

should_ken_respond判断：
- 评论有一定深度或引发思考
- 提出了有价值的观点或疑问
- 不是简单的"赞同"或"很好"
"""
            
            messages = [
                LlmMessage(role="system", content=system_prompt),
                LlmMessage(role="user", content=user_prompt)
            ]
            response = send_chat_completion(
                config=self.llm_config,
                messages=messages,
                temperature=0.3,
                max_tokens=300
            )
            
            result = self._parse_comment_moderation(response)
            
            logger.info(f"评论审核完成: action={result['action']}")
            
            return result
            
        except Exception as e:
            logger.error(f"评论审核失败: {e}")
            return {
                'action': 'reject',
                'reason': '审核系统异常',
                'safety_score': 0,
                'should_ken_respond': False
            }
    
    def _parse_moderation_result(self, response: str) -> Dict[str, Any]:
        """解析问题审核结果"""
        try:
            # 尝试从响应中提取JSON
            response = response.strip()
            
            # 如果响应被包裹在markdown代码块中
            if response.startswith('```'):
                lines = response.split('\n')
                response = '\n'.join(lines[1:-1])
            
            data = json.loads(response)
            
            # 验证必需字段
            return {
                'action': data.get('action', 'reject'),
                'reason': data.get('reason', ''),
                'ken_wang_feedback': data.get('ken_wang_feedback', ''),
                'safety_score': int(data.get('safety_score', 0)),
                'quality_score': int(data.get('quality_score', 0)),
                'worthy_of_article': bool(data.get('worthy_of_article', False)),
                'estimated_length': data.get('estimated_length', 'short'),
                'details': json.dumps({
                    'concerns': data.get('concerns', []),
                    'suggestions': data.get('suggestions', []),
                    'ken_wang_feedback': data.get('ken_wang_feedback', '')
                }, ensure_ascii=False)
            }
            
        except json.JSONDecodeError:
            logger.warning(f"无法解析审核结果为JSON: {response}")
            # 尝试基于关键词判断
            response_lower = response.lower()
            
            if 'reject' in response_lower or '拒绝' in response_lower:
                action = 'reject'
            elif 'approve' in response_lower or '通过' in response_lower:
                action = 'approve'
            else:
                action = 'reject'
            
            return {
                'action': action,
                'reason': '审核完成',
                'ken_wang_feedback': '审核结果解析异常' if action == 'reject' else '',
                'safety_score': 5,
                'quality_score': 5,
                'worthy_of_article': action == 'approve',
                'estimated_length': 'medium',
                'details': json.dumps({'raw_response': response}, ensure_ascii=False)
            }
    
    def _parse_comment_moderation(self, response: str) -> Dict[str, Any]:
        """解析评论审核结果"""
        try:
            response = response.strip()
            
            if response.startswith('```'):
                lines = response.split('\n')
                response = '\n'.join(lines[1:-1])
            
            data = json.loads(response)
            
            return {
                'action': data.get('action', 'reject'),
                'reason': data.get('reason', ''),
                'safety_score': int(data.get('safety_score', 0)),
                'should_ken_respond': bool(data.get('should_ken_respond', False))
            }
            
        except json.JSONDecodeError:
            logger.warning(f"无法解析评论审核结果: {response}")
            
            response_lower = response.lower()
            action = 'approve' if ('approve' in response_lower or '通过' in response_lower) else 'reject'
            
            return {
                'action': action,
                'reason': '审核完成',
                'safety_score': 5,
                'should_ken_respond': False
            }
