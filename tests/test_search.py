from pathlib import Path
import pandas as pd
import pytest

from backend.app.loader import IndexLoadError, load_index
from backend.app.search import SearchIndex, tokenize
from backend.app.versioning import IndexManager


def make_version(root: Path, version: str = "v1.0.0") -> Path:
    directory = root / version
    directory.mkdir(parents=True)
    pd.DataFrame([{"document_id": "1", "title": "Cats", "content": "Cats are friendly animals", "url": "/cats"}, {"document_id": "2", "title": "Dogs", "content": "Dogs are friendly pets", "url": "/dogs"}]).to_parquet(directory / "documents.parquet")
    pd.DataFrame([{"term": "cats", "document_id": "1", "term_frequency": 1}, {"term": "friendly", "document_id": "1", "term_frequency": 1}, {"term": "friendly", "document_id": "2", "term_frequency": 1}, {"term": "dogs", "document_id": "2", "term_frequency": 1}]).to_parquet(directory / "inverted_index.parquet")
    pd.DataFrame([{"document_id": "1", "pagerank": 0.2}, {"document_id": "2", "pagerank": 0.8}]).to_parquet(directory / "pagerank.parquet")
    return directory


def test_tokenize_and_search_ranking(tmp_path):
    index = load_index(make_version(tmp_path), "v1.0.0")
    assert tokenize("Cats, FRIENDLY!") == ["cats", "friendly"]
    response = index.search("cats")
    assert response["total"] == 1
    assert response["results"][0]["id"] == "1"
    assert response["results"][0]["score"] == pytest.approx(1.0)


def test_missing_files_and_reload_preserves_active_index(tmp_path):
    make_version(tmp_path)
    manager = IndexManager(tmp_path)
    assert manager.active_version == "v1.0.0"
    (tmp_path / "broken").mkdir()
    with pytest.raises(IndexLoadError):
        manager.reload("broken")
    assert manager.active_version == "v1.0.0"


def test_invalid_columns(tmp_path):
    directory = tmp_path / "v1"
    directory.mkdir()
    pd.DataFrame([{"wrong": "x"}]).to_parquet(directory / "documents.parquet")
    with pytest.raises(IndexLoadError, match="missing columns"):
        load_index(directory, "v1")
