from pathlib import Path
from typing import Any
import pandas as pd

from .search import Document, SearchIndex, tokenize


class IndexLoadError(RuntimeError):
    pass


def _read_required(path: Path, columns: set[str]) -> pd.DataFrame:
    if not path.is_file():
        raise IndexLoadError(f"Missing required export: {path.name}")
    try:
        frame = pd.read_parquet(path)
    except Exception as exc:
        raise IndexLoadError(f"Unable to read {path.name}: {exc}") from exc
    missing = columns - set(frame.columns)
    if missing:
        raise IndexLoadError(f"{path.name} is missing columns: {', '.join(sorted(missing))}")
    return frame


def load_index(version_dir: Path, version: str) -> SearchIndex:
    documents_frame = _read_required(version_dir / "documents.parquet", {"document_id", "title", "content"})
    inverted_frame = _read_required(version_dir / "inverted_index.parquet", {"term", "document_id", "term_frequency"})
    pagerank_frame = _read_required(version_dir / "pagerank.parquet", {"document_id", "pagerank"})
    documents: dict[str, Document] = {}
    for row in documents_frame.drop_duplicates("document_id").to_dict("records"):
        document_id = str(row["document_id"])
        documents[document_id] = Document(document_id, str(row["title"]), str(row["content"]), str(row["url"]) if row.get("url") is not None else None, {key: value for key, value in row.items() if key not in {"document_id", "title", "content", "url"}})
    postings: dict[str, dict[str, int]] = {}
    for row in inverted_frame.to_dict("records"):
        term = str(row["term"]).lower()
        document_id = str(row["document_id"])
        if document_id in documents:
            postings.setdefault(term, {})[document_id] = int(row["term_frequency"])
    pagerank = {str(row["document_id"]): float(row["pagerank"]) for row in pagerank_frame.drop_duplicates("document_id").to_dict("records") if str(row["document_id"]) in documents}
    if not documents:
        raise IndexLoadError("documents.parquet contains no documents")
    return SearchIndex(documents, postings, pagerank, version)
