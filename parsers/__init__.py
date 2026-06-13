import importlib
import logging
import pkgutil

from . import registry

__all__ = ["registry"]


def _discover():
    """Auto-import all sub-packages to trigger @register decorators."""
    for importer, modname, ispkg in pkgutil.iter_modules(__path__):
        if ispkg:
            try:
                importlib.import_module(f"{__name__}.{modname}")
            except Exception:
                logging.error("Failed to import parser package %s", modname, exc_info=True)


_discover()
