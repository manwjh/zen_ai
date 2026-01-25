"""
KenWang 评论处理器

职责：
1. 决定是否回复某条评论
2. 生成个性化的评论回复
3. 体现"有些嗤之以鼻，有些真诚回应"的人性化特点
"""

import json
import logging
import random
from typing import Dict, Any, Optional
from ..llm import LlmMessage, send_chat_completion, LLMConfig
from .identity import get_identity_for_comment

logger = logging.getLogger(__name__)


class CommentHandler:
    """评论处理器"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
    
    def should_respond(
        self, 
        comment: str,
        article_title: str,
        is_mentioned: bool = False,
        language: str = 'zh'
    ) -> bool:
        """
        判断是否应该回复这条评论
        
        参数：
            comment: 评论内容
            article_title: 文章标题
            is_mentioned: 是否@KenWang
            language: 语言
        
        返回：
            True/False
        """
        try:
            # 如果被@，更倾向于回复（但不是必然）
            if is_mentioned:
                # 被@时，70%概率回复
                if random.random() < 0.7:
                    return self._evaluate_comment_quality(comment, language)
                else:
                    logger.info(f"被@但KenWang选择不回复")
                    return False
            else:
                # 未被@时，20%概率回复
                if random.random() < 0.2:
                    return self._evaluate_comment_quality(comment, language)
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"判断是否回复时出错: {e}")
            return False
    
    def generate_response(
        self,
        comment: str,
        article_title: str,
        article_summary: str,
        thread: list = None,
        is_mentioned: bool = False,
        language: str = 'zh'
    ) -> Optional[Dict[str, Any]]:
        """
        生成评论回复
        
        参数：
            comment: 评论内容
            article_title: 文章标题
            article_summary: 文章摘要
            thread: N级跟帖上下文（父评论列表）
            is_mentioned: 是否@KenWang
            language: 语言
        
        返回：
        {
            'response': str,
            'tone': 'encouraging' | 'thoughtful' | 'challenging' | 'dismissive'
        }
        """
        try:
            # 构建提示词
            system_prompt = get_identity_for_comment(language)
            
            mentioned_text = "（此人@了你）" if is_mentioned else ""
            
            # 构建评论线索上下文
            thread_context = ""
            if thread and len(thread) > 0:
                thread_context = "\n\n【评论线索】（从根评论到当前评论的对话）：\n"
                for i, parent in enumerate(thread, 1):
                    thread_context += f"{i}楼 {parent.get('user_display_name', 'Unknown')}: {parent.get('content', '')}\n"
                thread_context += f"{len(thread) + 1}楼 当前评论: {comment}\n"
            
            user_prompt = f"""有人在你的文章《{article_title}》下评论{mentioned_text}：
{thread_context}
{'当前' if thread else ''}评论："{comment}"

文章主旨：{article_summary}

请以KenWang的身份决定如何回复。你有多种回复风格：

1. **真诚回应**（对有深度、真诚的评论）
   - 给予鼓励和进一步启发
   - 分享更多思考或故事
   - 展现温暖和智慧

2. **点到为止**（对一般性评论）
   - 简短回应
   - 稍加点拨
   - 不过度展开

3. **善意挑战**（对有偏颇但不恶意的观点）
   - 指出思维局限
   - 提供另一种视角
   - 保持尊重但不妥协

4. **嗤之以鼻**（对肤浅、炫技、装腔作势的评论）
   - 不正面回应
   - 可用"😏"、"有意思"等简短回应
   - 或者完全不理

请按照以下JSON格式返回：
{{
    "should_respond": true或false,
    "response": "回复内容（如果should_respond为false，留空）",
    "tone": "encouraging/thoughtful/challenging/dismissive",
    "internal_note": "你的内心想法（不会展示给用户）"
}}

注意：
- 如果评论质量太低，can say should_respond=false
- 回复要简洁，一般不超过150字
- 保持KenWang的个性：有智慧、有态度、有人情味
- 不要过度说教，点到为止
"""
            
            # 调用LLM
            messages = [
                LlmMessage(role="system", content=system_prompt),
                LlmMessage(role="user", content=user_prompt)
            ]
            response = send_chat_completion(
                config=self.llm_config,
                messages=messages,
                temperature=0.8,  # 评论需要一定个性
                max_tokens=500
            )
            
            # 解析响应
            result = self._parse_response(response)
            
            if not result.get('should_respond'):
                logger.info("KenWang决定不回复此评论")
                return None
            
            logger.info(f"KenWang回复: tone={result['tone']}")
            
            return {
                'response': result['response'],
                'tone': result['tone']
            }
            
        except Exception as e:
            logger.error(f"生成评论回复失败: {e}")
            return None
    
    def _evaluate_comment_quality(self, comment: str, language: str) -> bool:
        """
        快速评估评论质量
        
        简单启发式规则，避免频繁调用LLM
        """
        # 太短的评论（如"赞"、"好"）不回复
        if len(comment) < 10:
            return False
        
        # 包含问号的评论更可能回复（表示有疑问）
        if '?' in comment or '？' in comment:
            return True
        
        # 较长且有实质内容的评论
        if len(comment) > 50:
            return True
        
        # 其他情况随机
        return random.random() < 0.3
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析回复响应"""
        try:
            response = response.strip()
            
            if response.startswith('```'):
                lines = response.split('\n')
                start_idx = 1 if lines[0].startswith('```') else 0
                end_idx = -1 if lines[-1].strip() == '```' else None
                response = '\n'.join(lines[start_idx:end_idx])
            
            data = json.loads(response)
            
            return {
                'should_respond': bool(data.get('should_respond', True)),
                'response': data.get('response', ''),
                'tone': data.get('tone', 'thoughtful'),
                'internal_note': data.get('internal_note', '')
            }
            
        except json.JSONDecodeError:
            logger.warning(f"无法解析评论回复JSON: {response[:100]}")
            
            # 如果解析失败，尝试直接使用响应文本
            if len(response) > 20 and len(response) < 500:
                return {
                    'should_respond': True,
                    'response': response,
                    'tone': 'thoughtful',
                    'internal_note': 'parsed from raw text'
                }
            else:
                return {
                    'should_respond': False,
                    'response': '',
                    'tone': 'dismissive',
                    'internal_note': 'parse failed'
                }
    
    def get_dismissive_response(self) -> str:
        """获取一个"嗤之以鼻"式的简短回复"""
        responses = [
            "😏",
            "有意思。",
            "是吗。",
            "嗯。",
            "随你。",
            "如此甚好。",
            "..."
        ]
        return random.choice(responses)
