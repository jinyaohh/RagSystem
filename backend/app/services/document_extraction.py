"""
Document extraction service for processing various file types.

Supports PDF, DOCX, Excel, and plain text files.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pdfplumber
import pypdf
from docx import Document as DocxDocument
import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentExtractionService:
    """Service for extracting text from various document formats."""

    def __init__(self):
        """Initialize document extraction service."""
        logger.info("Initialized DocumentExtractionService")

    async def extract_text(
        self,
        file_path: Path,
        file_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract text from document.

        Args:
            file_path: Path to document file
            file_type: File type (pdf, docx, xlsx, txt). Auto-detected if None.

        Returns:
            Dict with:
                - text: Extracted text content
                - metadata: Document metadata (pages, author, etc.)

        Raises:
            ValueError: If file type is not supported
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Auto-detect file type if not provided
        if file_type is None:
            file_type = file_path.suffix.lstrip('.').lower()

        logger.info(f"Extracting text from {file_type.upper()} file: {file_path.name}")

        # Route to appropriate extractor
        if file_type == 'pdf':
            return await self._extract_from_pdf(file_path)
        elif file_type in ['docx', 'doc']:
            return await self._extract_from_docx(file_path)
        elif file_type in ['xlsx', 'xls']:
            return await self._extract_from_excel(file_path)
        elif file_type == 'txt':
            return await self._extract_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    async def _extract_from_pdf(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract text from PDF file.

        Uses pdfplumber for better text extraction quality.
        Falls back to pypdf if pdfplumber fails.
        """
        try:
            text_parts = []
            metadata = {}

            with pdfplumber.open(file_path) as pdf:
                # Extract metadata
                metadata = {
                    'num_pages': len(pdf.pages),
                    'metadata': pdf.metadata or {},
                }

                # Extract text from each page
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()

                    if page_text:
                        # Add page marker for citation
                        text_parts.append(f"[Page {page_num}]\n{page_text}\n")

                    # Log progress for large documents
                    if page_num % 10 == 0:
                        logger.debug(f"Processed {page_num}/{len(pdf.pages)} pages")

            full_text = "\n".join(text_parts)

            logger.info(
                f"Extracted {len(full_text)} characters from "
                f"{metadata['num_pages']} pages"
            )

            return {
                'text': full_text,
                'metadata': metadata,
            }

        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}, trying pypdf")

            # Fallback to pypdf
            try:
                return await self._extract_from_pdf_pypdf(file_path)
            except Exception as fallback_error:
                logger.error(f"PDF extraction failed: {fallback_error}")
                raise

    async def _extract_from_pdf_pypdf(self, file_path: Path) -> Dict[str, Any]:
        """Fallback PDF extraction using pypdf."""
        text_parts = []

        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)

            metadata = {
                'num_pages': len(pdf_reader.pages),
                'metadata': pdf_reader.metadata or {},
            }

            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()

                if page_text:
                    text_parts.append(f"[Page {page_num}]\n{page_text}\n")

        full_text = "\n".join(text_parts)

        logger.info(f"Extracted {len(full_text)} characters using pypdf")

        return {
            'text': full_text,
            'metadata': metadata,
        }

    async def _extract_from_docx(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from DOCX file."""
        try:
            doc = DocxDocument(file_path)

            # Extract text from paragraphs
            text_parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)

            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = ' | '.join(cell.text.strip() for cell in row.cells)
                    if row_text.strip():
                        text_parts.append(row_text)

            full_text = "\n\n".join(text_parts)

            metadata = {
                'num_paragraphs': len(doc.paragraphs),
                'num_tables': len(doc.tables),
                'core_properties': {
                    'author': doc.core_properties.author,
                    'created': str(doc.core_properties.created) if doc.core_properties.created else None,
                    'modified': str(doc.core_properties.modified) if doc.core_properties.modified else None,
                    'title': doc.core_properties.title,
                }
            }

            logger.info(
                f"Extracted {len(full_text)} characters from DOCX "
                f"({metadata['num_paragraphs']} paragraphs, {metadata['num_tables']} tables)"
            )

            return {
                'text': full_text,
                'metadata': metadata,
            }

        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            raise

    async def _extract_from_excel(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from Excel file."""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)

            text_parts = []
            sheet_info = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # Convert dataframe to text representation
                sheet_text = f"[Sheet: {sheet_name}]\n"
                sheet_text += df.to_string(index=False)
                text_parts.append(sheet_text)

                sheet_info.append({
                    'name': sheet_name,
                    'rows': len(df),
                    'columns': len(df.columns),
                })

            full_text = "\n\n".join(text_parts)

            metadata = {
                'num_sheets': len(excel_file.sheet_names),
                'sheets': sheet_info,
            }

            logger.info(
                f"Extracted {len(full_text)} characters from Excel "
                f"({metadata['num_sheets']} sheets)"
            )

            return {
                'text': full_text,
                'metadata': metadata,
            }

        except Exception as e:
            logger.error(f"Excel extraction failed: {e}")
            raise

    async def _extract_from_txt(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()

            metadata = {
                'encoding': 'utf-8',
                'size_bytes': file_path.stat().st_size,
            }

            logger.info(f"Read {len(text)} characters from text file")

            return {
                'text': text,
                'metadata': metadata,
            }

        except UnicodeDecodeError:
            # Try with different encoding
            logger.warning("UTF-8 decoding failed, trying latin-1")
            with open(file_path, 'r', encoding='latin-1') as file:
                text = file.read()

            metadata = {
                'encoding': 'latin-1',
                'size_bytes': file_path.stat().st_size,
            }

            return {
                'text': text,
                'metadata': metadata,
            }

    def get_supported_formats(self) -> list[str]:
        """
        Get list of supported file formats.

        Returns:
            List of supported file extensions
        """
        return ['pdf', 'docx', 'doc', 'xlsx', 'xls', 'txt']

    def is_supported_format(self, file_type: str) -> bool:
        """
        Check if file format is supported.

        Args:
            file_type: File extension (without dot)

        Returns:
            True if supported, False otherwise
        """
        return file_type.lower() in self.get_supported_formats()
