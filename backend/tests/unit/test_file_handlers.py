"""
文件处理工具单元测试
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.utils.file_handlers import (
    FileHandler, TextFileHandler, MarkdownFileHandler,
    DocxFileHandler, EpubFileHandler, FileProcessingError,
    get_file_handler
)
from src.models.project import SupportedFileType


class TestFileHandler:
    """FileHandler基类测试"""

    @pytest.fixture
    def sample_text_file(self):
        """创建示例文本文件"""
        content = "这是一个测试文件。\n包含多行内容。"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        yield temp_path
        os.unlink(temp_path)

    def test_validate_file_txt_success(self, sample_text_file):
        """测试验证TXT文件成功"""
        file_info = FileHandler.validate_file(sample_text_file)

        assert file_info['file_type'] == SupportedFileType.TXT
        assert file_info['file_size'] > 0
        assert file_info['is_supported'] is True

    def test_validate_file_unsupported_extension(self):
        """测试验证不支持的文件扩展名"""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            temp_path = f.name

        try:
            file_info = FileHandler.validate_file(temp_path)
            assert file_info['is_supported'] is False
        finally:
            os.unlink(temp_path)

    def test_validate_file_nonexistent(self):
        """测试验证不存在的文件"""
        with pytest.raises(FileProcessingError):
            FileHandler.validate_file('/nonexistent/file.txt')

    def test_save_temp_file(self):
        """测试保存临时文件"""
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.file = Mock()
        mock_file.file.seek = Mock()
        mock_file.file.write = Mock()
        mock_file.file.flush = Mock()

        # 模拟文件读取
        content = b"test content"
        mock_file.file.read.return_value = content
        mock_file.file.seek.return_value = len(content)

        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value = mock_temp.return_value
            mock_temp.return_value.__enter__.return_value.name = "/tmp/test.txt"
            mock_temp.return_value.__enter__.return_value.write = Mock()

            path, filename = FileHandler.save_temp_file(mock_file)

            assert filename == "test.txt"
            assert path.endswith("test.txt")

    def test_get_file_handler_txt(self):
        """测试获取TXT文件处理器"""
        handler = get_file_handler(SupportedFileType.TXT)
        assert isinstance(handler, TextFileHandler)

    def test_get_file_handler_md(self):
        """测试获取MD文件处理器"""
        handler = get_file_handler(SupportedFileType.MD)
        assert isinstance(handler, MarkdownFileHandler)

    def test_get_file_handler_unsupported(self):
        """测试获取不支持的文件类型处理器"""
        with pytest.raises(FileProcessingError):
            get_file_handler(None)


class TestTextFileHandler:
    """TextFileHandler测试"""

    @pytest.fixture
    def text_handler(self):
        return TextFileHandler()

    @pytest.fixture
    def sample_text_content(self):
        return """这是一个测试文档。

包含多个段落。

- 列表项1
- 列表项2
- 列表项3

这是最后一个段落。"""

    def test_read_text_file_success(self, text_handler, sample_text_content):
        """测试读取文本文件成功"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(sample_text_content)
            temp_path = f.name

        try:
            content = text_handler.read_text_file(temp_path)
            assert content == sample_text_content
        finally:
            os.unlink(temp_path)

    def test_count_words(self, text_handler):
        """测试字数统计"""
        text = "Hello world! This is a test."
        word_count = text_handler.count_words(text)
        assert word_count == 6

    def test_count_words_empty(self, text_handler):
        """测试空文本字数统计"""
        word_count = text_handler.count_words("")
        assert word_count == 0

    def test_count_paragraphs(self, text_handler):
        """测试段落数统计"""
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        paragraph_count = text_handler.count_paragraphs(text)
        assert paragraph_count == 3

    def test_count_sentences(self, text_handler):
        """测试句子数统计"""
        text = "First sentence. Second sentence! Third sentence?"
        sentence_count = text_handler.count_sentences(text)
        assert sentence_count >= 3

    def test_count_sentences_empty(self, text_handler):
        """测试空文本句子数统计"""
        sentence_count = text_handler.count_sentences("")
        assert sentence_count == 0


class TestMarkdownFileHandler:
    """MarkdownFileHandler测试"""

    @pytest.fixture
    def md_handler(self):
        return MarkdownFileHandler()

    @pytest.fixture
    def sample_markdown_content(self):
        return """# 标题

这是一个测试文档。

## 二级标题

这是一个段落。

### 三级标题

- 列表项1
- 列表项2
- 列表项3

**粗体文本** 和 *斜体文本*

```python
print("Hello, World!")
```
"""

    def test_read_markdown_file_success(self, md_handler, sample_markdown_content):
        """测试读取Markdown文件成功"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(sample_markdown_content)
            temp_path = f.name

        try:
            content = md_handler.read_markdown_file(temp_path)
            assert content == sample_markdown_content
        finally:
            os.unlink(temp_path)

    def test_extract_metadata(self, md_handler, sample_markdown_content):
        """测试提取Markdown元数据"""
        metadata = md_handler.extract_metadata(sample_markdown_content)

        assert 'title_count' in metadata
        assert 'header_count' in metadata
        assert 'code_block_count' in metadata
        assert 'link_count' in metadata

    def test_extract_chapters(self, md_handler):
        """测试提取章节信息"""
        content = """# 第一章

第一章内容...

## 1.1 小节

小节内容...

# 第二章

第二章内容...

## 2.1 小节

小节内容...
"""
        chapters = md_handler.extract_chapters(content)

        assert len(chapters) == 2
        assert chapters[0]['title'] == '第一章'
        assert chapters[1]['title'] == '第二章'


@pytest.mark.asyncio
class TestDocxFileHandler:
    """DocxFileHandler测试"""

    @pytest.fixture
    def docx_handler(self):
        return DocxFileHandler()

    async def test_read_docx_file_mock(self, docx_handler):
        """测试读取DOCX文件（使用Mock）"""
        with patch('docx.Document') as mock_docx:
            mock_document = Mock()
            mock_paragraph = Mock()
            mock_paragraph.text = "测试段落内容"
            mock_document.paragraphs = [mock_paragraph]
            mock_docx.return_value = mock_document

            # 注意：这里假设DocxFileHandler会临时保存文件到磁盘
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
                temp_path = f.name
                f.write(b"mock docx content")

            try:
                # 需要实现DocxFileHandler.read_docx_file方法
                # content = await docx_handler.read_docx_file(temp_path)
                # assert content == "测试段落内容"
                pass  # 暂时跳过，因为需要实现具体方法
            finally:
                os.unlink(temp_path)

    async def test_validate_docx_structure_mock(self, docx_handler):
        """测试DOCX文件结构验证"""
        # 这里需要实现具体的验证逻辑
        pass


@pytest.mark.asyncio
class TestEpubFileHandler:
    """EpubFileHandler测试"""

    @pytest.fixture
    def epub_handler(self):
        return EpubFileHandler()

    async def test_read_epub_file_mock(self, epub_handler):
        """测试读取EPUB文件（使用Mock）"""
        with patch('ebooklib.epub.read_epub') as mock_read:
            mock_book = Mock()
            mock_book.title = "测试电子书"
            mock_book.get_metadata = Mock(return_value=['测试作者'])
            mock_read.return_value = mock_book

            with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as f:
                temp_path = f.name
                f.write(b"mock epub content")

            try:
                # 需要实现EpubFileHandler.read_epub_file方法
                # metadata = await epub_handler.read_epub_file(temp_path)
                # assert metadata['title'] == "测试电子书"
                pass  # 暂时跳过
            finally:
                os.unlink(temp_path)

    async def test_extract_epub_chapters_mock(self, epub_handler):
        """测试提取EPUB章节"""
        # 这里需要实现具体的章节提取逻辑
        pass


class TestFileHandlerIntegration:
    """文件处理器集成测试"""

    def test_end_to_end_txt_processing(self):
        """测试TXT文件端到端处理"""
        content = """# 测试文档

这是一个测试段落。

另一个段落。
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        try:
            # 验证文件
            file_info = FileHandler.validate_file(temp_path)
            assert file_info['file_type'] == SupportedFileType.TXT

            # 获取处理器
            handler = get_file_handler(SupportedFileType.TXT)
            assert isinstance(handler, TextFileHandler)

            # 读取内容
            read_content = handler.read_text_file(temp_path)
            assert read_content == content

            # 统计信息
            word_count = handler.count_words(read_content)
            paragraph_count = handler.count_paragraphs(read_content)

            assert word_count > 0
            assert paragraph_count >= 2

        finally:
            os.unlink(temp_path)

    def test_unsupported_file_handling(self):
        """测试不支持的文件处理"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"mock pdf content")
            temp_path = f.name

        try:
            # 验证文件
            file_info = FileHandler.validate_file(temp_path)
            assert file_info['is_supported'] is False

            # 尝试获取处理器应该失败
            with pytest.raises(FileProcessingError):
                get_file_handler(None)

        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__])