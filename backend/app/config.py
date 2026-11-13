from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    active_version: str | None
    allow_admin_reload: bool
    host: str
    port: int


def get_settings() -> Settings:
    data_dir = Path(os.getenv("ATLAS_DATA_DIR", "data/versions")).expanduser()
    active_version = os.getenv("ATLAS_ACTIVE_VERSION") or None
    return Settings(
        data_dir=data_dir,
        active_version=active_version,
        allow_admin_reload=os.getenv("ATLAS_ALLOW_ADMIN_RELOAD", "false").lower() == "true",
        host=os.getenv("ATLAS_HOST", "127.0.0.1"),
        port=int(os.getenv("ATLAS_PORT", "8000")),
    )
