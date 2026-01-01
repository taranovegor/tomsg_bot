from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class FileInfo:
    """Immutable file metadata."""

    path: Path
    size: int
    mime_type: Optional[str] = None
    original_url: Optional[str] = None
