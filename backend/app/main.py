from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .loader import IndexLoadError
from .versioning import IndexManager


settings = get_settings()
app = FastAPI(title="AtlasSearch VM4", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
try:
    manager = IndexManager(settings.data_dir, settings.active_version)
    startup_error = None
except IndexLoadError as exc:
    manager = None
    startup_error = str(exc)


def get_manager() -> IndexManager:
    if manager is None:
        raise HTTPException(status_code=503, detail=f"Index unavailable: {startup_error}")
    return manager


@app.get("/")
def root():
    return {"name": "AtlasSearch", "component": "VM4 search", "version": app.version}


@app.get("/health")
def health():
    return {"status": "ok" if manager else "degraded", "index_loaded": manager is not None, "active_version": manager.active_version if manager else None, "error": startup_error}


@app.get("/search")
def search(q: str = Query(..., min_length=1, max_length=500), limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)):
    return get_manager().index.search(q, limit, offset)


@app.get("/documents/{document_id}")
def document(document_id: str):
    found = get_manager().index.documents.get(document_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"id": found.document_id, "title": found.title, "content": found.content, "url": found.url, "metadata": found.metadata or {}}


@app.get("/stats")
def stats():
    index = get_manager().index
    return {"version": index.version, "documents": len(index.documents), "terms": len(index.postings), "postings": sum(len(items) for items in index.postings.values()), "pagerank_documents": len(index.pagerank), "average_document_length": index.average_document_length}


@app.get("/versions")
def versions():
    current = get_manager()
    return {"active_version": current.active_version, "versions": current.versions()}


@app.post("/admin/reload")
def reload_index(version: str | None = None):
    if not settings.allow_admin_reload:
        raise HTTPException(status_code=403, detail="Admin reload is disabled")
    try:
        loaded = get_manager().reload(version)
    except IndexLoadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"status": "reloaded", "active_version": loaded.version}
