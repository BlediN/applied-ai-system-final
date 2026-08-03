from __future__ import annotations

from dataclasses import dataclass
from collections import Counter, defaultdict
from math import sqrt, log
from typing import Iterable

from .corpus import Chunk, tokenize


@dataclass(frozen=True)
class RetrievalResult:
    chunk: Chunk
    score: float


class Retriever:
    def __init__(self, chunks: Iterable[Chunk]) -> None:
        self._chunks = list(chunks)
        if not self._chunks:
            raise ValueError("Retriever requires at least one chunk.")

        self._chunk_vectors: list[dict[str, float]] = []
        self._chunk_norms: list[float] = []
        document_frequency: defaultdict[str, int] = defaultdict(int)

        for chunk in self._chunks:
            terms = Counter(tokenize(chunk.text))
            if not terms:
                self._chunk_vectors.append({})
                self._chunk_norms.append(0.0)
                continue

            for term in terms:
                document_frequency[term] += 1

            self._chunk_vectors.append(dict(terms))

        total_chunks = len(self._chunks)
        self._idf = {
            term: log((1 + total_chunks) / (1 + frequency)) + 1.0
            for term, frequency in document_frequency.items()
        }

        for vector in self._chunk_vectors:
            norm = sqrt(sum((count * self._idf.get(term, 0.0)) ** 2 for term, count in vector.items()))
            self._chunk_norms.append(norm)

    @property
    def chunks(self) -> list[Chunk]:
        return list(self._chunks)

    def search(self, query: str, top_k: int = 3) -> list[RetrievalResult]:
        query_terms = Counter(tokenize(query))
        if not query_terms:
            return []

        query_vector = {
            term: count * self._idf.get(term, 0.0)
            for term, count in query_terms.items()
        }
        query_norm = sqrt(sum(weight * weight for weight in query_vector.values()))
        if query_norm == 0.0:
            return []

        scored: list[RetrievalResult] = []
        for chunk, vector, chunk_norm in zip(self._chunks, self._chunk_vectors, self._chunk_norms):
            if not vector or chunk_norm == 0.0:
                continue

            numerator = 0.0
            for term, query_weight in query_vector.items():
                numerator += query_weight * vector.get(term, 0) * self._idf.get(term, 0.0)

            score = numerator / (chunk_norm * query_norm)
            if score > 0.0:
                scored.append(RetrievalResult(chunk=chunk, score=score))

        scored.sort(key=lambda result: result.score, reverse=True)
        return scored[:top_k]
