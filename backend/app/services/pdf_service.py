"""
PDF parsing service.
Extracts clean text from uploaded PDF files using pypdf.
Handles multi-page documents and basic text cleanup.
"""

import logging
import re
from pathlib import Path
from typing import Tuple

from pypdf import PdfReader

from app.core.exceptions import FileProcessingError

logger = logging.getLogger(__name__)


class PDFService:
    """
    Handles all PDF file operations:
    - Validating PDF files
    - Extracting text from all pages
    - Cleaning extracted text
    """

    @staticmethod
    def extract_text(file_path: str) -> Tuple[str, int]:
        """
        Extract all text from a PDF file.

        Args:
            file_path: Absolute path to the PDF file

        Returns:
            Tuple of (extracted_text, page_count)

        Raises:
            FileProcessingError: If the file cannot be read or parsed
        """
        path = Path(file_path)

        if not path.exists():
            raise FileProcessingError(
                message=f"File not found: {file_path}",
                details="The uploaded file could not be located on disk"
            )

        if path.suffix.lower() != ".pdf":
            raise FileProcessingError(
                message=f"Invalid file type: {path.suffix}",
                details="Only PDF files are supported"
            )

        try:
            reader = PdfReader(str(path))
            page_count = len(reader.pages)

            if page_count == 0:
                raise FileProcessingError(
                    message="PDF has no pages",
                    details="The uploaded PDF appears to be empty"
                )

            full_text_parts = []
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        full_text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Could not extract text from page {page_num + 1}: {e}")
                    continue

            if not full_text_parts:
                raise FileProcessingError(
                    message="No text could be extracted from PDF",
                    details="The PDF may be scanned/image-based without OCR text"
                )

            raw_text = "\n\n".join(full_text_parts)
            cleaned_text = PDFService._clean_text(raw_text)

            logger.info(f"Extracted {len(cleaned_text)} chars from {page_count} pages: {path.name}")
            return cleaned_text, page_count

        except FileProcessingError:
            raise
        except Exception as e:
            raise FileProcessingError(
                message=f"Failed to parse PDF: {str(e)}",
                details=f"File: {path.name}"
            )

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean extracted PDF text by removing artifacts.
        - Collapse excessive whitespace
        - Remove non-printable characters
        - Normalize line breaks
        """
        # Remove non-printable characters except newlines and tabs
        text = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]', ' ', text)
        # Collapse multiple spaces into one
        text = re.sub(r'[ \t]+', ' ', text)
        # Collapse more than 2 consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Strip leading/trailing whitespace
        text = text.strip()
        return text

    @staticmethod
    def validate_file_size(file_size_bytes: int, max_mb: int) -> None:
        """
        Validate that an uploaded file does not exceed the size limit.

        Raises:
            FileProcessingError: If file is too large
        """
        max_bytes = max_mb * 1024 * 1024
        if file_size_bytes > max_bytes:
            raise FileProcessingError(
                message=f"File too large: {file_size_bytes / (1024*1024):.1f}MB",
                details=f"Maximum allowed size is {max_mb}MB"
            )


pdf_service = PDFService()
