"""Document processing utilities.

This module provides functionality for processing different document
types and extracting text content for the RAG system.

When an image_dir is provided, images embedded in the document are
extracted to disk, and a placeholder like [图片: img_xxx.png] is
inserted at the image's original position in the text so that later
chunking keeps the image reference attached to its surrounding text.
"""

import hashlib
import os
import re
import logging
from typing import List, Optional
from dataclasses import dataclass, field

from app.utils.text_splitter import TextSplitter, TextChunk

logger = logging.getLogger(__name__)

# 匹配图片占位符，用于分块后回填 chunk 元数据
IMAGE_PLACEHOLDER_RE = re.compile(r'\[图片: (img_[0-9a-f]+\.\w+)\]')

# 图片魔数与浏览器可展示的扩展名对照（EMF/WMF 等无法在浏览器渲染，直接跳过）
_IMAGE_MAGIC_EXTENSIONS = (
    (b'\x89PNG', '.png'),
    (b'\xff\xd8\xff', '.jpg'),
    (b'GIF8', '.gif'),
    (b'BM', '.bmp'),
    (b'RIFF', '.webp'),
)


@dataclass
class ProcessedDocument:
    """Represents a processed document with its chunks."""

    filename: str
    content: str
    chunks: List[TextChunk]
    metadata: dict
    # 文档内提取到的全部图片文件名（去重后）
    images: List[str] = field(default_factory=list)


class DocumentProcessor:
    """Document processor for extracting and chunking text from files.

    Supports:
    - Plain text files (.txt)
    - PDF files (.pdf)
    - Word documents (.docx)
    """

    SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.docx'}

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """Initialize the document processor.

        Args:
            chunk_size: Target size for each chunk in characters.
            chunk_overlap: Number of characters to overlap between chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = TextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def process_file(
        self,
        file_path: str,
        metadata: Optional[dict] = None,
        image_dir: Optional[str] = None
    ) -> ProcessedDocument:
        """Process a file and return its processed content.

        Args:
            file_path: Path to the file.
            metadata: Optional metadata to include.
            image_dir: Optional directory to save extracted images to.
                When given, embedded images are saved to disk and
                referenced in the text via [图片: filename] placeholders.

        Returns:
            ProcessedDocument with content and chunks.

        Raises:
            ValueError: If file type is not supported.
            FileNotFoundError: If file does not exist.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {ext}. "
                f"Supported types: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        # Extract text based on file type
        if ext == '.txt':
            content = self._extract_text_from_txt(file_path)
        elif ext == '.pdf':
            content = self._extract_text_from_pdf(file_path, image_dir)
        elif ext == '.docx':
            content = self._extract_text_from_docx(file_path, image_dir)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        # Chunk the content
        chunks = self.text_splitter.split_text(content)

        # 回填每个 chunk 引用的图片文件名，供检索时返回原图
        extracted_images = IMAGE_PLACEHOLDER_RE.findall(content)
        for chunk in chunks:
            chunk_images = IMAGE_PLACEHOLDER_RE.findall(chunk.content)
            if chunk_images:
                chunk.metadata = {'images': chunk_images}

        # Create metadata
        filename = os.path.basename(file_path)
        file_metadata = {
            'filename': filename,
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'file_type': ext,
        }
        if metadata:
            file_metadata.update(metadata)

        logger.info(
            f"Processed {filename}: {len(content)} chars, "
            f"{len(chunks)} chunks, {len(extracted_images)} image refs"
        )

        return ProcessedDocument(
            filename=filename,
            content=content,
            chunks=chunks,
            metadata=file_metadata,
            images=extracted_images
        )

    def _save_image(self, blob: bytes, image_dir: str) -> Optional[str]:
        """Save an image blob to image_dir, deduplicated by content hash.

        Args:
            blob: Raw image bytes.
            image_dir: Directory to save the image to.

        Returns:
            Saved filename, or None if the format is not renderable
            in a browser (e.g. EMF/WMF).
        """
        ext = None
        for magic, extension in _IMAGE_MAGIC_EXTENSIONS:
            if blob.startswith(magic):
                ext = extension
                break
        if ext is None:
            logger.debug(f"Skipping unsupported image format ({len(blob)} bytes)")
            return None

        # 内容哈希命名：同一文档里重复出现的 logo/装饰图只存一份
        digest = hashlib.sha1(blob).hexdigest()[:12]
        filename = f"img_{digest}{ext}"
        path = os.path.join(image_dir, filename)
        if not os.path.exists(path):
            os.makedirs(image_dir, exist_ok=True)
            with open(path, 'wb') as f:
                f.write(blob)
        return filename

    def _extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from a plain text file.

        Args:
            file_path: Path to the text file.

        Returns:
            Extracted text content.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _extract_text_from_pdf(
        self, file_path: str, image_dir: Optional[str] = None
    ) -> str:
        """Extract text from a PDF file.

        Args:
            file_path: Path to the PDF file.
            image_dir: Optional directory to save embedded images to.

        Returns:
            Extracted text content.
        """
        try:
            import pypdf
        except ImportError:
            logger.warning("pypdf not installed, trying PyPDF2")
            try:
                import PyPDF2 as pypdf
            except ImportError:
                raise ImportError(
                    "PDF extraction requires pypdf or PyPDF2. "
                    "Install with: pip install pypdf"
                )

        text_parts = []

        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

                # 提取当前页的图片，占位符紧跟正文，保持图文相对位置
                if image_dir:
                    try:
                        for image in page.images:
                            filename = self._save_image(image.data, image_dir)
                            if filename:
                                text_parts.append(f"\n[图片: {filename}]\n")
                    except Exception as e:
                        # 个别 PDF 的图片流无法解析，不应阻断文本提取
                        logger.warning(f"Failed to extract images from PDF page: {e}")

        return "\n\n".join(text_parts)

    def _extract_text_from_docx(
        self, file_path: str, image_dir: Optional[str] = None
    ) -> str:
        """Extract text from a Word document.

        Walks the document body in order (paragraphs and tables interleaved),
        so that inline images are replaced with placeholders at their
        original position and table text is not silently dropped.

        Args:
            file_path: Path to the .docx file.
            image_dir: Optional directory to save embedded images to.

        Returns:
            Extracted text content.
        """
        try:
            from docx import Document
            from docx.table import Table
            from docx.text.paragraph import Paragraph
            from docx.oxml.ns import qn
        except ImportError:
            raise ImportError(
                "Word document extraction requires python-docx. "
                "Install with: pip install python-docx"
            )

        doc = Document(file_path)
        text_parts = []

        # doc.paragraphs 只含顶层段落，表格内容需单独遍历；
        # 按 body 子元素顺序迭代，保证段落与表格的相对位置不变
        for child in doc.element.body.iterchildren():
            if child.tag == qn('w:p'):
                paragraph = Paragraph(child, doc)
                para_text = self._paragraph_text_with_images(doc, paragraph, image_dir)
                if para_text.strip():
                    text_parts.append(para_text)
            elif child.tag == qn('w:tbl'):
                table_text = self._table_text(Table(child, doc))
                if table_text.strip():
                    text_parts.append(table_text)

        return "\n\n".join(text_parts)

    def _paragraph_text_with_images(
        self, doc, paragraph, image_dir: Optional[str]
    ) -> str:
        """Extract paragraph text, replacing inline images with placeholders.

        Args:
            doc: The python-docx Document (for relationship lookup).
            paragraph: The Paragraph object.
            image_dir: Optional directory to save embedded images to.

        Returns:
            Paragraph text with image placeholders.
        """
        para_parts = []
        for run in paragraph.runs:
            para_parts.append(run.text or "")

            # 内联图片：w:drawing 内的 a:blip 通过 r:embed 关联图片部件
            if image_dir:
                try:
                    for blip in run._element.findall(
                        './/{http://schemas.openxmlformats.org/drawingml/2006/main}blip'
                    ):
                        rid = blip.get(
                            '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed'
                        )
                        if rid and rid in doc.part.rels:
                            image_part = doc.part.rels[rid].target_part
                            filename = self._save_image(
                                image_part.blob, image_dir
                            )
                            if filename:
                                para_parts.append(f"\n[图片: {filename}]\n")
                except Exception as e:
                    logger.warning(f"Failed to extract image from docx run: {e}")

        return "".join(para_parts)

    def _table_text(self, table) -> str:
        """Extract table text as lines, one row per line.

        Args:
            table: The python-docx Table object.

        Returns:
            Table text joined by newlines.
        """
        lines = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            # 跳过整行重复（合并单元格会产生重复单元格引用）
            deduped = []
            for c in cells:
                if c and (not deduped or deduped[-1] != c):
                    deduped.append(c)
            if deduped:
                lines.append(" ".join(deduped))
        return "\n".join(lines)

    def process_text(
        self,
        text: str,
        filename: str = "text",
        metadata: Optional[dict] = None
    ) -> ProcessedDocument:
        """Process plain text content.

        Args:
            text: Text content to process.
            filename: Virtual filename for the content.
            metadata: Optional metadata to include.

        Returns:
            ProcessedDocument with content and chunks.
        """
        chunks = self.text_splitter.split_text(text)

        file_metadata = {
            'filename': filename,
            'file_type': '.txt',
        }
        if metadata:
            file_metadata.update(metadata)

        return ProcessedDocument(
            filename=filename,
            content=text,
            chunks=chunks,
            metadata=file_metadata
        )

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get list of supported file extensions.

        Returns:
            List of supported file extensions.
        """
        return list(cls.SUPPORTED_EXTENSIONS)

    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """Check if a file type is supported.

        Args:
            file_path: Path to the file.

        Returns:
            True if file type is supported, False otherwise.
        """
        _, ext = os.path.splitext(file_path)
        return ext.lower() in cls.SUPPORTED_EXTENSIONS