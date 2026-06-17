import importlib
import logging

DEFAULT_LOCALE = "ru"
SUPPORTED_LOCALES = {"ru", "en"}

_catalogs: dict[str, dict[str, str]] = {}


def normalize_locale(locale: str | None) -> str:
    if not locale:
        return DEFAULT_LOCALE
    base = locale.replace("-", "_").split("_")[0]
    return base if base in SUPPORTED_LOCALES else DEFAULT_LOCALE


def _load_catalog(locale: str) -> dict[str, str]:
    if locale not in _catalogs:
        try:
            mod = importlib.import_module(f".locales.{locale}", package=__package__)
            _catalogs[locale] = mod.translations
        except (ImportError, AttributeError):
            _catalogs[locale] = {}
    return _catalogs[locale]


def t(key: str, locale: str | None = None) -> str:
    locale = normalize_locale(locale)
    catalog = _load_catalog(locale)
    if key in catalog:
        return catalog[key]
    if locale != DEFAULT_LOCALE:
        fallback = _load_catalog(DEFAULT_LOCALE)
        if key in fallback:
            return fallback[key]
    logging.warning("Missing translation key: %s (locale=%s)", key, locale)
    return key
