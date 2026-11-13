from collections import defaultdict
from dataclasses import dataclass
import math
import re
from typing import Any


TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


@dataclass(frozen=True)
class Document:
    document_id: str
    title: str
    content: str
    url: str | None = None
    metadata: dict[str, Any] | None = None


class SearchIndex:
    def __init__(self, documents: dict[str, Document], postings: dict[str, dict[str, int]], pagerank: dict[str, float], version: str):
        self.documents = documents
        self.postings = postings
        self.pagerank = pagerank
        self.version = version
        self.document_lengths = {doc_id: sum(postings_for_doc.values()) for doc_id, postings_for_doc in self._by_document().items()}
        self.average_document_length = sum(self.document_lengths.values()) / len(documents) if documents else 0.0

    def _by_document(self) -> dict[str, dict[str, int]]:
        result: dict[str, dict[str, int]] = defaultdict(dict)
        for term, term_postings in self.postings.items():
            for document_id, frequency in term_postings.items():
                result[document_id][term] = frequency
        return result

    def candidates(self, query_tokens: list[str]) -> set[str]:
        return {document_id for token in set(query_tokens) for document_id in self.postings.get(token, {})}

    def bm25(self, query_tokens: list[str], document_id: str, k1: float = 1.2, b: float = 0.75) -> float:
        if not query_tokens or document_id not in self.documents:
            return 0.0
        length = self.document_lengths.get(document_id, 0)
        score = 0.0
        for token in set(query_tokens):
            term_postings = self.postings.get(token, {})
            frequency = term_postings.get(document_id, 0)
            if not frequency:
                continue
            document_frequency = len(term_postings)
            idf = math.log(1 + (len(self.documents) - document_frequency + 0.5) / (document_frequency + 0.5))
            normalizer = frequency + k1 * (1 - b + b * length / self.average_document_length) if self.average_document_length else 1
            score += idf * frequency * (k1 + 1) / normalizer
        return score

    def search(self, query: str, limit: int = 10, offset: int = 0) -> dict[str, Any]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return {"query": query, "tokens": [], "total": 0, "results": [], "version": self.version}
        candidate_ids = self.candidates(query_tokens)
        bm25_scores = {doc_id: self.bm25(query_tokens, doc_id) for doc_id in candidate_ids}
        max_bm25 = max(bm25_scores.values(), default=0.0)
        rank_scores = {doc_id: self.pagerank.get(doc_id, 0.0) for doc_id in candidate_ids}
        max_rank = max(rank_scores.values(), default=0.0)
        ranked = []
        for doc_id in candidate_ids:
            bm25_component = bm25_scores[doc_id] / max_bm25 if max_bm25 else 0.0
            rank_component = rank_scores[doc_id] / max_rank if max_rank else 0.0
            final_score = 0.7 * bm25_component + 0.3 * rank_component
            document = self.documents[doc_id]
            ranked.append({
                "id": document.document_id,
                "title": document.title,
                "snippet": make_snippet(document.content, query_tokens),
                "url": document.url,
                "score": final_score,
                "bm25_score": bm25_scores[doc_id],
                "pagerank": rank_scores[doc_id],
            })
        ranked.sort(key=lambda item: (-item["score"], item["title"].lower(), item["id"]))
        return {"query": query, "tokens": query_tokens, "total": len(ranked), "results": ranked[offset:offset + limit], "version": self.version}


def make_snippet(content: str, query_tokens: list[str], length: int = 240) -> str:
    text = " ".join(content.split())
    positions = [text.lower().find(token) for token in query_tokens if text.lower().find(token) >= 0]
    start = max(0, min(positions, default=0) - 60)
    snippet = text[start:start + length]
    return ("..." if start else "") + snippet + ("..." if start + length < len(text) else "")
