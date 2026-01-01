from dataclasses import dataclass

from pathlib import Path
from typing import Optional


@dataclass
class VideoMeta:
    """Stores metadata for a video."""

    width: Optional[int]
    height: Optional[int]
    duration: Optional[int] = None
