"""
问题生成器 - 为心镜台自动生成高质量的种子问题

使用LLM生成关于人生、生活、健康、家庭、社会等主题的深度问题
"""

import json
import logging
import random
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..llm import LlmMessage, send_chat_completion, LLMConfig

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """智能问题生成器"""
    
    # 主题类别和子类别
    TOPICS = {
        "人生": [
            "意义与价值", "选择与决策", "目标与方向", 
            "成长与蜕变", "困境与突破", "平衡与取舍"
        ],
        "生活": [
            "日常习惯", "时间管理", "情绪管理", 
            "人际关系", "兴趣爱好", "生活质量"
        ],
        "健康": [
            "身体健康", "心理健康", "运动健身", 
            "饮食营养", "睡眠休息", "压力管理"
        ],
        "家庭": [
            "亲子关系", "夫妻关系", "代际沟通", 
            "家庭教育", "家庭和谐", "责任与爱"
        ],
        "社会": [
            "职场发展", "人际交往", "社会观察", 
            "时代变迁", "科技影响", "价值观念"
        ]
    }
    
    # 问题类型
    QUESTION_TYPES = [
        "困惑求解型",  # "我应该如何..."
        "现象观察型",  # "为什么现在..."
        "经验分享型",  # "如何看待..."
        "深度思考型",  # "什么是真正的..."
        "实践指导型",  # "怎样才能..."
    ]
    
    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
    
    def generate_question(
        self, 
        topic_category: Optional[str] = None,
        subtopic: Optional[str] = None,
        question_type: Optional[str] = None,
        language: str = 'zh'
    ) -> Dict[str, Any]:
        """
        生成一个问题
        
        参数：
            topic_category: 主题类别（人生/生活/健康/家庭/社会），None为随机
            subtopic: 子主题，None为随机
            question_type: 问题类型，None为随机
            language: 语言
        
        返回：
        {
            'question': str,
            'category': str,
            'subtopic': str,
            'type': str,
            'complexity': 'simple' | 'medium' | 'complex',
            'estimated_length': 'short' | 'medium' | 'long',
            'tags': List[str],
            'metadata': Dict
        }
        """
        try:
            # 随机选择主题（如果未指定）
            if not topic_category:
                topic_category = random.choice(list(self.TOPICS.keys()))
            
            if not subtopic:
                subtopic = random.choice(self.TOPICS[topic_category])
            
            if not question_type:
                question_type = random.choice(self.QUESTION_TYPES)
            
            # 构建提示词
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_generation_prompt(
                topic_category, subtopic, question_type, language
            )
            
            # 调用LLM
            messages = [
                LlmMessage(role="system", content=system_prompt),
                LlmMessage(role="user", content=user_prompt)
            ]
            response = send_chat_completion(
                config=self.llm_config,
                messages=messages,
                temperature=0.8,  # 创造性生成
                max_tokens=800
            )
            
            # 解析响应
            result = self._parse_generation_response(response)
            
            # 补充元数据
            result['category'] = topic_category
            result['subtopic'] = subtopic
            result['type'] = question_type
            result['generated_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"生成问题: {result['question'][:50]}... "
                       f"[{topic_category}/{subtopic}]")
            
            return result
            
        except Exception as e:
            logger.error(f"生成问题失败: {e}")
            raise
    
    def generate_batch(
        self, 
        count: int = 5, 
        diversify: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量生成问题
        
        参数：
            count: 生成数量
            diversify: 是否多样化（不同主题）
        
        返回：
            问题列表
        """
        questions = []
        
        if diversify:
            # 多样化：确保覆盖不同主题
            categories = list(self.TOPICS.keys())
            for i in range(count):
                category = categories[i % len(categories)]
                try:
                    question = self.generate_question(topic_category=category)
                    questions.append(question)
                except Exception as e:
                    logger.error(f"批量生成第{i+1}个问题失败: {e}")
                    continue
        else:
            # 自然分布
            for i in range(count):
                try:
                    question = self.generate_question()
                    questions.append(question)
                except Exception as e:
                    logger.error(f"批量生成第{i+1}个问题失败: {e}")
                    continue
        
        logger.info(f"批量生成完成: {len(questions)}/{count} 个问题")
        
        return questions
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一个善于提出深刻问题的思考者。

你的任务是生成能够引发深度思考和讨论的问题，这些问题将由KenWang（一位下山入世的智者）来回答。

优质问题的特征：
1. 具有普遍性 - 不是过于私人化的问题
2. 有深度 - 触及本质，而非表面
3. 真诚 - 来自真实的困惑或观察
4. 简洁 - 表达清晰，不啰嗦
5. 有讨论价值 - 能引发思考和共鸣

避免的问题类型：
- 过于私人琐碎的问题
- 纯粹的技术问题
- 是非判断题（"xx是对的吗？"）
- 封闭式问题（"要不要xx？"）
- 抱怨或发泄式问题

问题应该像一个真实的用户在向智者请教。"""
    
    def _build_generation_prompt(
        self, 
        category: str, 
        subtopic: str, 
        question_type: str,
        language: str
    ) -> str:
        """构建生成提示词"""
        
        type_descriptions = {
            "困惑求解型": "表达一个具体的困惑，寻求解决方法",
            "现象观察型": "观察到某个社会或生活现象，想了解背后的原因",
            "经验分享型": "询问如何看待某个话题或经历",
            "深度思考型": "探讨某个概念的本质或意义",
            "实践指导型": "寻求具体的实践建议或方法"
        }
        
        return f"""请生成一个关于【{category} - {subtopic}】的问题。

问题类型：{question_type}
类型说明：{type_descriptions[question_type]}

要求：
1. 问题长度：80-300字
2. 真实自然，像一个真实用户的提问
3. 具有一定深度和讨论价值
4. 符合指定的问题类型特征

请按照以下JSON格式返回：
{{
    "question": "问题内容",
    "complexity": "simple 或 medium 或 complex",
    "estimated_length": "short 或 medium 或 long (预估KenWang回答的长度)",
    "tags": ["标签1", "标签2", "标签3"],
    "reasoning": "为什么这是一个好问题（不会展示给用户）"
}}

注意：
- complexity: simple=浅显易懂, medium=有一定深度, complex=需要深入探讨
- estimated_length: 预估KenWang回答需要的篇幅
- tags: 3-5个相关标签
- 问题要自然，不要太"教科书"

现在请生成问题："""
    
    def _parse_generation_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            response = response.strip()
            
            # 移除可能的markdown代码块
            if response.startswith('```'):
                lines = response.split('\n')
                start_idx = 1 if lines[0].startswith('```') else 0
                end_idx = -1 if lines[-1].strip() == '```' else None
                response = '\n'.join(lines[start_idx:end_idx])
            
            data = json.loads(response)
            
            # 验证必需字段
            required_fields = ['question', 'complexity', 'estimated_length', 'tags']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"缺少必需字段: {field}")
            
            return {
                'question': data['question'],
                'complexity': data['complexity'],
                'estimated_length': data['estimated_length'],
                'tags': data.get('tags', []),
                'reasoning': data.get('reasoning', ''),
                'metadata': {
                    'raw_response': response[:200]
                }
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"无法解析生成结果为JSON: {e}\n响应内容: {response[:200]}")
            
            # 回退：尝试从文本中提取问题
            # 假设问题在引号中或者是第一行
            question = response
            if '"' in response:
                import re
                match = re.search(r'"([^"]{50,})"', response)
                if match:
                    question = match.group(1)
            
            return {
                'question': question[:500],
                'complexity': 'medium',
                'estimated_length': 'medium',
                'tags': [],
                'reasoning': 'Parsed from fallback',
                'metadata': {'parse_error': str(e)}
            }
    
    def validate_question(self, question_text: str) -> Dict[str, Any]:
        """
        验证生成的问题质量
        
        返回：
        {
            'is_valid': bool,
            'score': int (1-10),
            'issues': List[str],
            'suggestions': List[str]
        }
        """
        issues = []
        suggestions = []
        score = 10
        
        # 长度检查
        if len(question_text) < 20:
            issues.append("问题太短")
            score -= 3
        elif len(question_text) > 500:
            issues.append("问题太长")
            score -= 2
        
        # 关键词检查（避免过于私人化）
        personal_keywords = ['我家', '我老公', '我老婆', '我孩子', '我妈', '我爸']
        if any(keyword in question_text for keyword in personal_keywords):
            issues.append("问题过于私人化")
            suggestions.append("建议改为更普遍的表达方式")
            score -= 2
        
        # 问号检查
        if '?' not in question_text and '？' not in question_text:
            issues.append("缺少问号")
            score -= 1
        
        is_valid = score >= 6 and len(issues) <= 2
        
        return {
            'is_valid': is_valid,
            'score': score,
            'issues': issues,
            'suggestions': suggestions
        }


# ========================================
# 预定义的主题灵感库
# ========================================

TOPIC_INSPIRATIONS = {
    "人生": [
        "中年危机的本质是什么？",
        "如何找到人生的意义？",
        "为什么我们总是陷入选择困难？",
        "什么是真正的成长？",
        "如何面对人生的不确定性？",
    ],
    "生活": [
        "如何培养一个好习惯？",
        "为什么我们总是拖延？",
        "怎样提升生活的幸福感？",
        "如何与自己的情绪和平相处？",
        "什么是高质量的生活？",
    ],
    "健康": [
        "如何在忙碌中保持健康？",
        "为什么现代人容易焦虑？",
        "怎样建立规律的运动习惯？",
        "如何改善睡眠质量？",
        "什么是真正的健康？",
    ],
    "家庭": [
        "如何与父母有效沟通？",
        "怎样平衡工作与家庭？",
        "如何教育孩子独立思考？",
        "为什么家庭关系会疏远？",
        "什么是好的亲子关系？",
    ],
    "社会": [
        "如何在职场中保持初心？",
        "为什么现代人越来越孤独？",
        "怎样建立有意义的人际关系？",
        "科技如何改变我们的生活？",
        "什么是值得追求的成功？",
    ]
}


def get_inspiration(category: Optional[str] = None) -> str:
    """获取一个灵感示例"""
    if category and category in TOPIC_INSPIRATIONS:
        return random.choice(TOPIC_INSPIRATIONS[category])
    else:
        all_inspirations = []
        for inspirations in TOPIC_INSPIRATIONS.values():
            all_inspirations.extend(inspirations)
        return random.choice(all_inspirations)
