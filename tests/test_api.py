from pathlib import Path
import pandas as pd


def write_fixture(root: Path):
    directory = root / "v1"
    directory.mkdir(parents=True)
    pd.DataFrame([{"document_id": "a", "title": "Alpha", "content": "alpha content"}]).to_parquet(directory / "documents.parquet")
    pd.DataFrame([{"term": "alpha", "document_id": "a", "term_frequency": 1}]).to_parquet(directory / "inverted_index.parquet")
    pd.DataFrame([{"document_id": "a", "pagerank": 1.0}]).to_parquet(directory / "pagerank.parquet")


def test_api_endpoints(tmp_path, monkeypatch):
    write_fixture(tmp_path)
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_VERSION", "v1")
    from backend.app import main
    main.settings = main.get_settings()
    main.manager = main.IndexManager(main.settings.data_dir, main.settings.active_version)
    assert main.health()["index_loaded"]
    assert main.search("alpha", 10, 0)["results"][0]["id"] == "a"
    assert main.document("a")["id"] == "a"
    assert main.stats()["documents"] == 1
