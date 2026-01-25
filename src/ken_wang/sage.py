"""
KenWang 智者文章生成器

职责：
1. 根据审核通过的问题生成文章
2. 根据estimated_length调整文章长度
3. 生成标题、正文、摘要
"""

import json
import logging
import time
from typing import Dict, Any
from ..llm import LlmMessage, send_chat_completion, LLMConfig
from .identity import get_identity_for_writing

logger = logging.getLogger(__name__)


class SageWriter:
    """智者文章生成器"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
    
    def write_article(
        self, 
        question: str, 
        estimated_length: str = 'medium',
        language: str = 'zh'
    ) -> Dict[str, Any]:
        """
        撰写文章
        
        参数：
            question: 问题内容
            estimated_length: 预估长度 (short/medium/long)
            language: 语言
        
        返回：
        {
            'title': str,
            'content': str (markdown),
            'summary': str,
            'word_count': int,
            'reading_time': int (秒),
            'tags': str (JSON array),
            'metadata': str (JSON),
            'model': str,
            'generation_time': int (毫秒)
        }
        """
        start_time = time.time()
        
        try:
            # 根据长度确定字数范围
            length_config = {
                'short': {
                    'target_words': 600,
                    'description': '简短文章（500-800字）',
                    'max_tokens': 1500
                },
                'medium': {
                    'target_words': 1500,
                    'description': '中等文章（1200-2000字）',
                    'max_tokens': 3000
                },
                'long': {
                    'target_words': 3000,
                    'description': '深度长文（2500-4000字）',
                    'max_tokens': 5000
                }
            }
            
            config = length_config.get(estimated_length, length_config['medium'])
            
            # 构建提示词
            system_prompt = get_identity_for_writing()
            
            # 根据语言生成不同的提示词
            user_prompt = self._build_writing_prompt(question, config, language)
            
            # 调用LLM
            messages = [
                LlmMessage(role="system", content=system_prompt),
                LlmMessage(role="user", content=user_prompt)
            ]
            response = send_chat_completion(
                config=self.llm_config,
                messages=messages,
                temperature=0.7,  # 创作需要一定创造性
                max_tokens=config['max_tokens']
            )
            
            # 解析响应
            article_data = self._parse_article_response(response)
            
            # 计算元数据
            word_count = len(article_data['content'])
            reading_time = self._estimate_reading_time(word_count, language)
            
            generation_time = int((time.time() - start_time) * 1000)
            
            result = {
                'title': article_data['title'],
                'content': article_data['content'],
                'summary': article_data['summary'],
                'word_count': word_count,
                'reading_time': reading_time,
                'tags': article_data['tags'],  # 保持为列表
                'metadata': {  # 保持为字典
                    'estimated_length': estimated_length,
                    'target_words': config['target_words'],
                    'actual_words': word_count,
                    'language': language
                },
                'model': self.llm_config.model,
                'generation_time': generation_time
            }
            
            logger.info(f"文章生成完成: {word_count}字, 用时{generation_time}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"文章生成失败: {e}")
            raise
    
    def _build_writing_prompt(self, question: str, config: dict, language: str) -> str:
        """构建写作提示词（根据语言）"""
        
        if language == 'en':
            return f"""Someone asked you:

"{question}"

As KenWang, please write an article ({config['description']}) to answer this question.

Requirements:
1. Title: Concise and powerful, capturing the core insight
2. Body:
   - Use Markdown format
   - Target word count: approximately {config['target_words']} words
   - Clear structure with proper paragraphing
   - Balance Zen wisdom with practical insight
   - Use stories, metaphors, or dialogues where appropriate
   - Avoid empty preaching; provide actionable advice
3. Summary: A concise 100-150 word overview

Please return in the following JSON format:
{{
    "title": "Article Title",
    "content": "Article body (Markdown format)",
    "summary": "Article summary",
    "tags": ["tag1", "tag2", "tag3"]
}}

Note:
- Use Markdown headers (##), paragraphs, lists in content
- Tags should reflect core themes (3-5 tags, in English)
- Maintain KenWang's personality: wise yet relatable
- ALL CONTENT INCLUDING TAGS MUST BE IN ENGLISH
"""
        else:
            # 中文及其他语言
            return f"""有人向你提问：

"{question}"

请以KenWang的身份，撰写一篇{config['description']}来回答这个问题。

要求：
1. 标题：简洁有力，能概括核心观点
2. 正文：
   - 使用Markdown格式
   - 目标字数：约{config['target_words']}字
   - 结构清晰，分段合理
   - 既有禅意又接地气
   - 可以用故事、比喻、对话等方式
   - 避免空洞说教，要有实际可操作的建议
3. 摘要：100-150字的精炼概括

请按照以下JSON格式返回：
{{
    "title": "文章标题",
    "content": "文章正文（Markdown格式）",
    "summary": "文章摘要",
    "tags": ["标签1", "标签2", "标签3"]
}}

注意：
- content中使用Markdown的标题(##)、段落、列表等格式
- 标签应该反映文章的核心主题（3-5个，使用中文）
- 保持KenWang的个性：既有智慧又有人情味
- 所有内容包括标签都应使用中文
"""
    
    def _parse_article_response(self, response: str) -> Dict[str, Any]:
        """解析文章响应"""
        try:
            response = response.strip()
            
            # 移除可能的markdown代码块包裹
            if response.startswith('```'):
                lines = response.split('\n')
                # 找到第一个和最后一个```的位置
                start_idx = 1 if lines[0].startswith('```') else 0
                end_idx = -1 if lines[-1].strip() == '```' else None
                response = '\n'.join(lines[start_idx:end_idx])
            
            data = json.loads(response)
            
            # 验证必需字段
            required_fields = ['title', 'content', 'summary']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"缺少必需字段: {field}")
            
            return {
                'title': data['title'],
                'content': data['content'],
                'summary': data['summary'],
                'tags': data.get('tags', [])
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"无法解析文章JSON: {e}\n响应内容: {response[:200]}")
            
            # 尝试从文本中提取
            # 这是备用方案，实际生产中应该让LLM重试
            lines = response.split('\n')
            
            title = "未命名文章"
            content = response
            summary = response[:150] + "..."
            
            # 简单的启发式提取
            for i, line in enumerate(lines[:10]):
                if line.strip() and not line.startswith('{'):
                    title = line.strip('#').strip()
                    content = '\n'.join(lines[i+1:])
                    break
            
            return {
                'title': title,
                'content': content,
                'summary': summary,
                'tags': []
            }
    
    def _estimate_reading_time(self, char_count: int, language: str) -> int:
        """
        估算阅读时间（秒）
        
        阅读速度（字符/分钟）：
        - 中文：400-600
        - 英文：200-250 (words)
        """
        if language in ['zh', 'zh-tw', 'ja']:
            # 中文、日文：每分钟500字符
            chars_per_minute = 500
        else:
            # 英文等：每分钟250词，假设平均5字符/词
            chars_per_minute = 250 * 5
        
        minutes = char_count / chars_per_minute
        seconds = int(minutes * 60)
        
        # 至少1分钟
        return max(seconds, 60)
