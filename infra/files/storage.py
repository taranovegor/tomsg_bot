import logging
from pathlib import Path


class LocalStorage:
    """Map relative names to filesystem paths under a root directory."""

    def __init__(self, root: Path):
        self.root = root

    def get_path(self, relative_name: str) -> Path:
        """Creates parent directories if missing."""
        path = self.root / relative_name
        path.parent.mkdir(parents=True, exist_ok=True)
        logging.debug("Resolved path in local storage: %s", path)
        return path
