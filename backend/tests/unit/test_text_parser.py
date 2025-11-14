"""
文本解析服务单元测试
"""

import pytest

from src.services.text_parser import (ParsedContent, RegexChapterDetector, TextParserService)


class TestRegexChapterDetector:
    """正则章节检测器测试"""

    def test_detect_chapters_chinese_numbered(self):
        """检测中文数字章节"""
        text = """
第一章 引言

这是第一章的内容。

第二章 基础概念

这是第二章的内容。

第三章 高级应用

这是第三章的内容。
        """.strip()

        detector = RegexChapterDetector()
        chapters = detector.detect_chapters(text)

        assert len(chapters) == 3
        assert "第一章" in chapters[0].title
        assert "第二章" in chapters[1].title
        assert "第三章" in chapters[2].title
        assert chapters[0].chapter_number == 1
        assert chapters[1].chapter_number == 2
        assert chapters[2].chapter_number == 3

    def test_detect_chapters_numbered(self):
        """检测数字章节"""
        text = """
1. 项目概述

这是项目概述内容。

2. 技术架构

这是技术架构内容。

3. 实现细节

这是实现细节内容。
        """.strip()

        detector = RegexChapterDetector()
        chapters = detector.detect_chapters(text)

        assert len(chapters) == 3
        assert "1." in chapters[0].title or "1、" in chapters[0].title
        assert chapters[0].chapter_number == 1

    def test_detect_chapters_english(self):
        """检测英文章节"""
        text = """
Chapter 1: Introduction

This is chapter 1 content.

Chapter 2: Methodology

This is chapter 2 content.
        """.strip()

        detector = RegexChapterDetector()
        chapters = detector.detect_chapters(text)

        assert len(chapters) == 2
        assert "Chapter 1" in chapters[0].title
        assert "Chapter 2" in chapters[1].title

    def test_detect_chapters_no_chapters(self):
        """检测无章节文本"""
        text = """
这是一段没有明确章节标记的文本。
它包含多个段落。
但没有章节标题。
        """.strip()

        detector = RegexChapterDetector()
        chapters = detector.detect_chapters(text)

        # 应该创建单个章节
        assert len(chapters) == 1
        assert chapters[0].title == "完整文档"
        assert chapters[0].detection_method == "fallback"

    def test_detect_chapters_empty_text(self):
        """测试空文本"""
        detector = RegexChapterDetector()
        chapters = detector.detect_chapters("")

        assert len(chapters) == 1
        assert chapters[0].title == "完整文档"
        assert chapters[0].content == ""


class TestTextParserService:
    """文本解析服务测试"""

    @pytest.fixture
    def parser_service(self):
        """创建解析服务实例"""
        return TextParserService()

    @pytest.mark.asyncio
    async def test_parse_document_basic(self, parser_service):
        """测试基础文档解析"""
        text = """
第一章 项目介绍

这是项目的介绍内容。

1.1 项目背景
项目背景是...

1.2 项目目标
项目目标是...

第二章 技术实现

这是技术实现的内容。
        """.strip()

        result = await parser_service.parse_document(text)

        assert isinstance(result, ParsedContent)
        assert len(result.chapters) >= 1
        assert len(result.paragraphs) >= 1
        assert len(result.sentences) >= 1
        assert result.processing_time > 0

    @pytest.mark.asyncio
    async def test_parse_document_empty(self, parser_service):
        """测试空文档解析"""
        from src.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            await parser_service.parse_document("")

    @pytest.mark.asyncio
    async def test_parse_document_long_text(self, parser_service):
        """测试长文档解析"""
        # 创建一个较长的文档
        text = "这是第一段。" * 100 + "\n\n" + "这是第二段。" * 100

        result = await parser_service.parse_document(text)

        assert len(result.chapters) >= 1
        assert len(result.paragraphs) >= 2
        assert result.processing_time < 10.0  # 应该在10秒内完成

    @pytest.mark.asyncio
    async def test_parse_to_models(self, parser_service):
        """测试解析为模型格式"""
        project_id = "test-project-id"
        text = """
第一章 测试章节

这是第一段。这是第一句。这是第二句。

这是第二段。这是第三句。
        """.strip()

        chapters_data, paragraphs_data, sentences_data = await parser_service.parse_to_models(
            project_id, text
        )

        # 验证章节数据
        assert len(chapters_data) == 1
        assert chapters_data[0]['project_id'] == project_id
        assert chapters_data[0]['title'] == "第一章 测试章节"
        assert chapters_data[0]['chapter_number'] == 1
        assert chapters_data[0]['paragraph_count'] == 2
        assert chapters_data[0]['sentence_count'] == 5  # 实际分割的句子数量

        # 验证段落数据
        assert len(paragraphs_data) == 2
        assert all(p['order_index'] in [1, 2] for p in paragraphs_data)
        assert all(p['action'] == 'keep' for p in paragraphs_data)

        # 验证句子的数据
        assert len(sentences_data) == 5  # 句子分割器实际分割的结果
        assert all(s['order_index'] in [1, 2, 3, 4, 5] for s in sentences_data)
        assert all(s['status'] == 'pending' for s in sentences_data)

    def test_get_detection_stats(self, parser_service):
        """测试获取检测统计"""
        stats = parser_service.get_detection_stats()

        assert 'total_documents_processed' in stats
        assert 'total_chapters_detected' in stats
        assert 'average_chapters_per_document' in stats
        assert isinstance(stats['total_documents_processed'], int)


if __name__ == "__main__":
    pytest.main([__file__])
