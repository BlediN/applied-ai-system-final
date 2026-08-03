from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

_WORD_RE = re.compile(r"[a-z0-9']+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_PARAGRAPH_RE = re.compile(r"\n\s*\n+")


@dataclass(frozen=True)
class Document:
    path: Path
    title: str
    text: str


@dataclass(frozen=True)
class Chunk:
    document_path: Path
    title: str
    text: str
    index: int


def load_documents(root: Path) -> list[Document]:
    if not root.exists():
        raise FileNotFoundError(f"Knowledge folder does not exist: {root}")

    documents: list[Document] = []
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in {".md", ".txt"} or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        title = path.stem.replace("_", " ").strip().title() or path.name
        documents.append(Document(path=path, title=title, text=text))

    if not documents:
        raise FileNotFoundError(
            f"No .md or .txt knowledge files were found in {root}. Add reference notes and try again."
        )

    return documents


def chunk_documents(documents: Iterable[Document], max_words: int = 120) -> list[Chunk]:
    chunks: list[Chunk] = []
    for document in documents:
        paragraphs = [part.strip() for part in _PARAGRAPH_RE.split(document.text) if part.strip()]
        if not paragraphs:
            paragraphs = [document.text]

        chunk_parts: list[str] = []
        word_count = 0
        index = 0

        for paragraph in paragraphs:
            paragraph_words = tokenize(paragraph)
            if not paragraph_words:
                continue

            if word_count and word_count + len(paragraph_words) > max_words:
                chunks.append(
                    Chunk(
                        document_path=document.path,
                        title=document.title,
                        text="\n\n".join(chunk_parts).strip(),
                        index=index,
                    )
                )
                index += 1
                chunk_parts = []
                word_count = 0

            if len(paragraph_words) > max_words:
                if chunk_parts:
                    chunks.append(
                        Chunk(
                            document_path=document.path,
                            title=document.title,
                            text="\n\n".join(chunk_parts).strip(),
                            index=index,
                        )
                    )
                    index += 1
                    chunk_parts = []
                    word_count = 0

                for sentence_group in _split_long_paragraph(paragraph, max_words):
                    chunks.append(
                        Chunk(
                            document_path=document.path,
                            title=document.title,
                            text=sentence_group,
                            index=index,
                        )
                    )
                    index += 1
                continue

            chunk_parts.append(paragraph)
            word_count += len(paragraph_words)

        if chunk_parts:
            chunks.append(
                Chunk(
                    document_path=document.path,
                    title=document.title,
                    text="\n\n".join(chunk_parts).strip(),
                    index=index,
                )
            )

    return chunks


def tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def sentence_split(text: str) -> list[str]:
    parts = [segment.strip() for segment in _SENTENCE_RE.split(text.strip()) if segment.strip()]
    return parts or [text.strip()]


def _split_long_paragraph(paragraph: str, max_words: int) -> list[str]:
    sentences = sentence_split(paragraph)
    groups: list[str] = []
    current: list[str] = []
    count = 0

    for sentence in sentences:
        sentence_words = tokenize(sentence)
        if current and count + len(sentence_words) > max_words:
            groups.append(" ".join(current).strip())
            current = []
            count = 0
        current.append(sentence)
        count += len(sentence_words)

    if current:
        groups.append(" ".join(current).strip())

    return groups
