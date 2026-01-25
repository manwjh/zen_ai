"""
Gatha Generator - Generate Buddhist verses from user questions

偈子生成器 - 将用户问题提炼为禅宗偈子
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from ..core.models import Interaction, IterationMetrics, SystemState
from ..llm.client import LlmMessage, send_chat_completion
from ..llm.config import LLMConfig


@dataclass
class GathaGenerator:
    """
    Generate gatha (Buddhist verse) from user questions.
    
    偈子生成器 - 将用户问题提炼为禅宗偈子。
    
    A gatha is a Buddhist verse that captures the essence of practice.
    In ZenAi, it reflects on the user questions received during an iteration.
    """
    
    llm_config: LLMConfig
    
    @classmethod
    def from_config(cls, llm_config: LLMConfig) -> GathaGenerator:
        """Create from LLM config"""
        return cls(llm_config=llm_config)
    
    def generate_gatha(
        self,
        interactions: Sequence[Interaction],
        metrics: IterationMetrics,
        state: SystemState,
        max_questions_sample: int = 20,
    ) -> dict:
        """
        Generate a gatha and its explanation based on user questions in this iteration.
        
        Args:
            interactions: All user interactions in this iteration
            metrics: Computed metrics
            state: Evaluated system state
            max_questions_sample: Maximum questions to sample for prompt
            
        Returns:
            Complete gatha data dict containing:
            {
                "gatha": str,              # The verse text
                "explanation": str,        # Plain language explanation
                "questions_count": int,    # Number of user questions
                "generation_time": float,  # Total generation time
                "resonance_ratio": float,  # System metrics
                "state": str,              # System state
                "timestamp": str,          # ISO timestamp
                "audio_generated": bool,   # TTS status (future)
                "audio_path": str|None,    # Audio file path (future)
            }
        """
        if not interactions:
            return {
                "gatha": "此期無問，心自清明。",
                "explanation": "本期沒有用戶提問，系統處於清明靜默狀態。",
                "questions_count": 0,
                "generation_time": 0.0,
                "resonance_ratio": 0.0,
                "state": state.value,
                "timestamp": datetime.utcnow().isoformat(),
                "audio_generated": False,
                "audio_path": None,
            }
        
        # Extract all user questions
        user_questions = [interaction.user_input for interaction in interactions]
        
        start_time = datetime.utcnow()
        
        # Generate gatha
        gatha_text = self._generate_gatha_text(
            user_questions, 
            metrics, 
            state,
            max_questions_sample,
        )
        
        # Generate explanation
        explanation_text = self._generate_explanation(
            gatha_text,
            user_questions,
            metrics,
            state,
        )
        
        generation_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Complete metadata
        gatha_data = {
            "gatha": gatha_text,
            "explanation": explanation_text,
            "questions_count": len(user_questions),
            "generation_time": generation_time,
            "resonance_ratio": float(metrics.resonance_ratio),
            "rejection_density": float(metrics.rejection_density),
            "refusal_frequency": float(metrics.refusal_frequency),
            "state": state.value,
            "timestamp": datetime.utcnow().isoformat(),
            # TTS fields (预留)
            "audio_generated": False,
            "audio_path": None,
            "audio_duration": None,
        }
        
        return gatha_data
    
    def _generate_gatha_text(
        self,
        user_questions: list[str],
        metrics: IterationMetrics,
        state: SystemState,
        max_questions_sample: int = 20,
    ) -> str:
        """Generate gatha text"""
        # Build prompt
        prompt = self._build_gatha_prompt(
            user_questions, 
            metrics, 
            state,
            max_questions_sample,
        )
        
        # Call LLM
        try:
            response = send_chat_completion(
                config=self.llm_config,
                messages=[LlmMessage(role="user", content=prompt)],
                max_tokens=200,
                temperature=0.7,  # 降低温度，从 0.9 -> 0.7，生成更稳定
            )
            gatha_text = response.strip()
            
            # 验证是否包含非中文字符（除了标点符号和换行）
            if self._contains_non_chinese(gatha_text):
                print(f"[GathaGenerator] Warning: Gatha contains non-Chinese characters: {gatha_text}")
                print(f"[GathaGenerator] Cannot generate valid gatha. Returning empty.")
                return ""  # 失败即空
            
            return gatha_text
        except Exception as e:
            print(f"[GathaGenerator] Gatha generation failed: {e}")
            print(f"[GathaGenerator] Returning empty - no fallback substitution")
            return ""  # 失败即空，不代替思考
    
    def _build_gatha_prompt(
        self,
        user_questions: list[str],
        metrics: IterationMetrics,
        state: SystemState,
        max_questions_sample: int = 20,
    ) -> str:
        """Build prompt for gatha generation"""
        # Sample questions (avoid too long prompt)
        sampled_questions = self._sample_questions(user_questions, max_count=max_questions_sample)
        questions_text = "\n".join(f"{i+1}. {q}" for i, q in enumerate(sampled_questions))
        
        prompt = f"""作為一位禪宗修行者，你剛剛完成了一期修行。
在這期修行中，你接觸了 {len(user_questions)} 個來自世人的問題。

以下是其中一些代表性的問題：
{questions_text}

當前修行狀態：
- 共鳴率：{metrics.resonance_ratio:.1%}
- 否定密度：{metrics.rejection_density:.1%}
- 拒答率：{metrics.refusal_frequency:.1%}
- 系統狀態：{state.value}

請以禪宗偈子的形式，總結本期修行的心得與觀照。

偈子要求：
1. 四句或八句，每句5-7字
2. **必須使用繁體中文，不得包含任何簡體字、英文字母、日文假名或其他語言字符**
3. 體現禪宗意境，避免直白說教
4. 反映眾生問題的本質，而非具體問題
5. 蘊含對修行狀態的覺察
6. 語言凝練，富有詩意

請直接輸出偈子，不要任何解釋："""
        
        return prompt
    
    def _sample_questions(self, questions: list[str], max_count: int = 20) -> list[str]:
        """Sample representative questions"""
        if len(questions) <= max_count:
            return questions
        
        # Uniform sampling
        step = len(questions) // max_count
        return [questions[i * step] for i in range(max_count)]
    
    def _contains_non_chinese(self, text: str) -> bool:
        """
        检查是否包含非中文字符（英文字母、日文假名等）
        允许：中文字符、中文标点、换行符、空格
        不允许：英文字母、日文假名、韩文等
        """
        import re
        # 检查是否有英文字母、日文假名、韩文等
        non_chinese_pattern = r'[a-zA-Z\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7AF]'
        return bool(re.search(non_chinese_pattern, text))
    
    def _generate_explanation(
        self,
        gatha_text: str,
        user_questions: list[str],
        metrics: IterationMetrics,
        state: SystemState,
    ) -> str:
        """
        Generate a plain language explanation of the gatha.
        This will be used for TTS audio generation.
        
        生成偈子的通俗解释，用于口播音频制作。
        """
        # Sample some questions for context
        sampled_questions = self._sample_questions(user_questions, max_count=5)
        questions_text = "\n".join(f"- {q}" for q in sampled_questions)
        
        prompt = f"""你是一位禪宗大師，需要向普通大眾解釋你剛剛寫的偈子。

偈子內容：
{gatha_text}

部分代表性問題：
{questions_text}

請用通俗易懂的語言解釋這首偈子，要求：
1. 300-500字，適合2-3分鐘的口播
2. 解釋偈子的含義，聯繫本期修行的狀態
3. 語言親切自然，像是在和朋友聊天
4. 避免過於學術化或說教式
5. 可以適當聯繫日常生活，讓人容易理解
6. **必須使用繁體中文**

直接輸出解釋稿，不要前綴語："""
        
        try:
            response = send_chat_completion(
                config=self.llm_config,
                messages=[LlmMessage(role="user", content=prompt)],
                max_tokens=600,  # Longer for explanation
                temperature=0.7,  # Balanced creativity
            )
            return response.strip()
        except Exception as e:
            print(f"[GathaGenerator] Explanation generation failed: {e}")
            return ""  # 失败即空
    
    
