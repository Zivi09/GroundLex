"""
Legal Document Ingestion Module
-------------------------------
Design Rationale for Legal Chunking Strategy:
Standard RAG implementations often rely on fixed character-count splitting (e.g., every 500 characters).
In legal domain applications, naive splitting destroys context boundaries—e.g., separating an 
Indemnification rule from its Exception sub-clause, or disconnecting a liability cap from its monetary limit.

This module implements a Clause-Aware Paragraph Chunker:
1. Retains page-level location metadata during PDF parsing with `pypdf`.
2. Hierarchically splits text prioritizing legal section/article delimiters (`\n\nSection `, `\n\nArticle `, `\n\n§`),
   followed by paragraph breaks (`\n\n`), sentence boundaries (`. `), and spaces.
3. Enforces ~300-500 token window (1200 characters) with 150-character overlap to preserve local context across chunk boundaries.
"""

import os
import re
from typing import List, Dict, Any
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

def extract_pages_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts text page-by-page from a PDF file.
    Returns a list of dicts containing page number, page text, and document name.
    """
    filename = os.path.basename(pdf_path)
    reader = PdfReader(pdf_path)
    pages_data = []

    for idx, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        # Clean excessive blank trailing spaces while preserving linebreaks
        cleaned_text = re.sub(r'[ \t]+', ' ', page_text).strip()
        
        if cleaned_text:
            pages_data.append({
                "doc_name": filename,
                "page_number": idx + 1,  # 1-indexed for human readability in citations
                "text": cleaned_text
            })

    return pages_data


def chunk_legal_document(pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Splits document pages into semantic, clause-preserving chunks.
    
    Why RecursiveCharacterTextSplitter with legal separators?
    Legal contracts follow strict hierarchy (Articles -> Sections -> Clauses -> Sub-clauses).
    By placing section and article headers at top priority in separator list, we ensure that
    individual sections remain whole whenever possible, producing self-contained semantic units.
    """
    legal_separators = [
        "\n\nSECTION ",
        "\n\nSection ",
        "\n\nARTICLE ",
        "\n\nArticle ",
        "\n\n§ ",
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=legal_separators,
        length_function=len
    )

    all_chunks = []
    global_chunk_idx = 0

    for page_info in pages_data:
        doc_name = page_info["doc_name"]
        page_num = page_info["page_number"]
        page_text = page_info["text"]

        raw_chunks = splitter.split_text(page_text)

        for chunk_text in raw_chunks:
            if not chunk_text.strip():
                continue

            all_chunks.append({
                "chunk_id": f"{doc_name}_p{page_num}_c{global_chunk_idx}",
                "text": chunk_text,
                "metadata": {
                    "doc_name": doc_name,
                    "page_number": page_num,
                    "chunk_index": global_chunk_idx,
                    "char_count": len(chunk_text),
                    "source": f"{doc_name} (Page {page_num})"
                }
            })
            global_chunk_idx += 1

    return all_chunks


def process_pdf_file(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Full ingestion pipeline: PDF -> Extracted Pages -> Clause Chunks with Metadata.
    """
    pages_data = extract_pages_from_pdf(pdf_path)
    chunks = chunk_legal_document(pages_data)
    return chunks
