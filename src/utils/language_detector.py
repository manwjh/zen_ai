"""
语言检测工具

用于检测文本的语言，并验证内容语言与声明语言是否匹配。
这是多语言社区语言隔离的核心组件。
"""

from langdetect import detect, DetectorFactory
from typing import Optional
import logging

# 确保检测结果可重复
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

# langdetect 返回的语言代码映射到我们的系统语言代码
LANGUAGE_MAP = {
    'zh-cn': 'zh',
    'zh-tw': 'zh-tw',
    'en': 'en',
    'ja': 'ja',
    'ko': 'ko'
}

# 语言名称（用于生成友好的错误消息）
LANGUAGE_NAMES = {
    'zh': '中文',
    'zh-tw': '繁体中文',
    'en': 'English',
    'ja': '日本語',
    'ko': '한국어'
}


def detect_language(text: str) -> Optional[str]:
    """
    检测文本的语言
    
    参数：
        text: 要检测的文本
    
    返回：
        - 'zh': 中文简体
        - 'zh-tw': 中文繁体  
        - 'en': 英文
        - 'ja': 日文
        - 'ko': 韩文
        - None: 检测失败
    
    示例：
        >>> detect_language("这是中文")
        'zh'
        >>> detect_language("This is English")
        'en'
    """
    if not text or len(text.strip()) < 10:
        logger.warning(f"文本太短，无法可靠检测语言: {text[:20]}")
        return None
    
    try:
        detected = detect(text)
        mapped = LANGUAGE_MAP.get(detected, detected)
        logger.debug(f"检测到语言: {detected} -> {mapped}")
        return mapped
    except Exception as e:
        logger.error(f"语言检测失败: {e}")
        return None


def verify_language_match(
    text: str, 
    declared_language: str,
    strict: bool = False
) -> bool:
    """
    验证文本语言是否与声明的语言匹配
    
    参数：
        text: 要检测的文本
        declared_language: 声明的语言（zh/en/ja/ko/zh-tw）
        strict: 是否严格模式（True=检测失败视为不匹配，False=检测失败视为匹配）
    
    返回：
        True: 语言匹配
        False: 语言不匹配
    
    示例：
        >>> verify_language_match("这是中文", "zh")
        True
        >>> verify_language_match("这是中文", "en")
        False
    """
    detected = detect_language(text)
    
    if not detected:
        # 检测失败的处理
        if strict:
            logger.warning(f"语言检测失败（严格模式），拒绝内容")
            return False
        else:
            logger.warning(f"语言检测失败（宽容模式），允许通过")
            return True
    
    # 简体中文和繁体中文互相兼容
    if declared_language in ['zh', 'zh-tw'] and detected in ['zh', 'zh-tw']:
        logger.debug(f"中文系列语言匹配: {detected} ≈ {declared_language}")
        return True
    
    # 严格匹配
    match = detected == declared_language
    logger.debug(f"语言匹配检查: {detected} {'==' if match else '!='} {declared_language}")
    return match


def get_language_mismatch_reason(text: str, declared_language: str) -> str:
    """
    生成语言不匹配的拒绝理由（用户友好的错误消息）
    
    参数：
        text: 检测的文本
        declared_language: 声明的语言
    
    返回：
        友好的错误消息
    
    示例：
        >>> get_language_mismatch_reason("这是中文", "en")
        '内容语言检测为中文，但您选择的语言区域是 English。请在正确的语言区域发布内容。'
    """
    detected = detect_language(text)
    
    declared_name = LANGUAGE_NAMES.get(declared_language, declared_language)
    
    if not detected:
        return f"无法检测内容语言。请确保您在 {declared_name} 区域使用正确的语言发布内容。"
    
    detected_name = LANGUAGE_NAMES.get(detected, detected)
    
    # 生成友好的多语言错误消息
    if declared_language == 'zh':
        return f"内容语言检测为 {detected_name}，但您选择的语言区域是{declared_name}。请在正确的语言区域发布内容。"
    elif declared_language == 'en':
        return f"Content language detected as {detected_name}, but you selected {declared_name} region. Please post in the correct language region."
    elif declared_language == 'ja':
        return f"コンテンツ言語が {detected_name} として検出されましたが、選択した言語領域は{declared_name}です。正しい言語領域で投稿してください。"
    elif declared_language == 'ko':
        return f"콘텐츠 언어가 {detected_name}(으)로 감지되었지만 선택한 언어 지역은 {declared_name}입니다. 올바른 언어 지역에 게시하십시오."
    else:
        return f"内容语言检测为 {detected_name}，但您选择的语言区域是{declared_name}。请在正确的语言区域发布内容。"


def get_language_name(language_code: str) -> str:
    """获取语言的友好名称"""
    return LANGUAGE_NAMES.get(language_code, language_code)


# 测试函数（用于开发验证）
def _test():
    """测试语言检测功能"""
    test_cases = [
        ("这是一段中文文本，用来测试语言检测功能。", "zh"),
        ("This is an English text for testing language detection.", "en"),
        ("これは日本語のテキストで、言語検出機能をテストするためのものです。", "ja"),
        ("이것은 언어 감지 기능을 테스트하기 위한 한국어 텍스트입니다.", "ko"),
        ("這是繁體中文文本，用於測試語言檢測功能。", "zh-tw"),
    ]
    
    print("=== 语言检测测试 ===\n")
    
    for text, expected in test_cases:
        detected = detect_language(text)
        match = verify_language_match(text, expected)
        
        print(f"文本: {text[:30]}...")
        print(f"预期: {expected}, 检测: {detected}, 匹配: {match}")
        print(f"错误消息: {get_language_mismatch_reason(text, 'en' if expected != 'en' else 'zh')}")
        print()


if __name__ == "__main__":
    _test()
