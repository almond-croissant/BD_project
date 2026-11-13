from pathlib import Path
from threading import RLock

from .loader import IndexLoadError, load_index
from .search import SearchIndex


class IndexManager:
    def __init__(self, data_dir: Path, active_version: str | None = None):
        self.data_dir = data_dir
        self._lock = RLock()
        self._index: SearchIndex | None = None
        self._active_version: str | None = None
        self.reload(active_version)

    def versions(self) -> list[str]:
        if not self.data_dir.is_dir():
            return []
        return sorted((item.name for item in self.data_dir.iterdir() if item.is_dir()), reverse=True)

    def reload(self, version: str | None = None) -> SearchIndex:
        candidates = [version] if version else self.versions()
        if not candidates:
            raise IndexLoadError(f"No index versions found in {self.data_dir}")
        errors = []
        for candidate in candidates:
            if candidate is None or Path(candidate).name != candidate:
                errors.append("invalid version name")
                continue
            try:
                loaded = load_index(self.data_dir / candidate, candidate)
            except IndexLoadError as exc:
                errors.append(str(exc))
                continue
            with self._lock:
                self._index = loaded
                self._active_version = candidate
            return loaded
        raise IndexLoadError("; ".join(errors))

    @property
    def index(self) -> SearchIndex:
        with self._lock:
            if self._index is None:
                raise IndexLoadError("No active index")
            return self._index

    @property
    def active_version(self) -> str | None:
        return self._active_version
