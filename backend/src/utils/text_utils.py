"""
文本处理工具函数 - 统一的文本处理模块
提供段落分割、句子分割、文本分析等功能，避免重复实现
严格按照data-model.md规范实现，为章节识别和解析提供支持
"""

import re
from dataclasses import dataclass
from typing import List

try:
    from src.core.logging import get_logger
except ImportError:
    # 用于独立测试的情况
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


@dataclass
class SentenceInfo:
    """句子信息"""
    text: str
    start_pos: int
    end_pos: int
    length: int
    word_count: int
    character_count: int


class ParagraphSplitter:
    """段落分割器 - 委托给file_handlers.py以避免重复代码"""

    @staticmethod
    def split_into_paragraphs(text: str) -> List[str]:
        """
        将文本分割为段落 - 委托给FileHandler
        保持接口兼容性，避免重复实现
        """
        if not text:
            return []
        return [p.strip() for p in text.split('\n\n') if p.strip()]


class SentenceSplitter:
    """句子分割器 - 专注于基础的句子分割功能"""

    def __init__(self):
        # 中文句子结束标记
        self.chinese_endings = r'[。！？…]'

        # 英文句子结束标记
        self.english_endings = r'[.!?]'

        # 编译正则表达式
        self.sentence_end_pattern = re.compile(
            rf'({self.chinese_endings}|{self.english_endings})+'
        )

        # 数字.数字模式（避免误判）
        self.decimal_pattern = re.compile(r'\d+\.\d+')

        # 缩写模式（英文）
        self.abbreviation_pattern = re.compile(
            r'\b(?:Mr|Mrs|Dr|Prof|St|etc|vs|e\.g|i\.e)\.$',
            re.IGNORECASE
        )

    def split_into_sentences(self, text: str) -> List[str]:
        """将文本分割为句子"""
        if not text:
            return []

        # 预处理文本
        processed_text = self._preprocess_text(text)

        # 基础句子分割
        sentences = self._basic_split(processed_text)

        # 后处理
        sentences = self._post_process_sentences(sentences)

        return sentences

    def split_sentences_with_info(self, text: str) -> List[SentenceInfo]:
        """分割句子并返回详细信息"""
        if not text or not text.strip():
            return []

        sentences = self.split_into_sentences(text)
        sentence_infos = []
        current_pos = 0

        for sentence in sentences:
            # 找到句子在原文中的位置
            start_pos = text.find(sentence, current_pos)
            if start_pos == -1:
                # 如果找不到，使用当前位置
                start_pos = current_pos

            end_pos = start_pos + len(sentence)

            sentence_info = SentenceInfo(
                text=sentence,
                start_pos=start_pos,
                end_pos=end_pos,
                length=len(sentence),
                word_count=self._count_words(sentence),
                character_count=len(sentence)
            )

            if sentence_info:
                sentence_infos.append(sentence_info)
                current_pos = end_pos

        return sentence_infos

    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 标准化空白字符
        text = re.sub(r'\s+', ' ', text)

        # 处理缩写
        text = self.abbreviation_pattern.sub(
            lambda m: m.group().replace('.', '<ABBREV_DOT>'),
            text
        )

        # 处理数字中的点
        text = self.decimal_pattern.sub(
            lambda m: m.group().replace('.', '<DECIMAL_DOT>'),
            text
        )

        return text

    def _basic_split(self, text: str) -> List[str]:
        """基础句子分割"""
        sentences = []

        # 使用正则表达式分割
        parts = self.sentence_end_pattern.split(text)

        # 重建句子
        for i in range(0, len(parts), 2):
            if i + 1 < len(parts):
                sentence = parts[i] + parts[i + 1]
            else:
                sentence = parts[i]

            sentence = sentence.strip()
            if sentence:
                sentences.append(sentence)

        return sentences

    def _post_process_sentences(self, sentences: List[str]) -> List[str]:
        """后处理句子列表"""
        processed = []

        for sentence in sentences:
            # 恢复被替换的字符
            sentence = sentence.replace('<ABBREV_DOT>', '.')
            sentence = sentence.replace('<DECIMAL_DOT>', '.')

            # 移除多余的空白
            sentence = re.sub(r'\s+', ' ', sentence).strip()

            if len(sentence) >= 5:  # 过滤过短的句子
                processed.append(sentence)

        return processed

    def _count_words(self, text: str) -> int:
        """
        计算词数 - 委托给FileHandler以避免重复实现
        保持接口兼容性，统一字数统计逻辑
        """
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        return chinese_chars + english_words


# 全局实例
paragraph_splitter = ParagraphSplitter()
sentence_splitter = SentenceSplitter()

__all__ = [
    'ParagraphSplitter',
    'SentenceSplitter',
    'SentenceInfo',
    'paragraph_splitter',
    'sentence_splitter'
]
