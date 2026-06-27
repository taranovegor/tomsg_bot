import logging

from . import locales

_CATALOGS: dict[str, dict[str, str]] = {
    name: getattr(locales, name).translations for name in locales.__all__
}

DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = set(_CATALOGS)


def normalize_locale(locale: str | None) -> str:
    if not locale:
        return DEFAULT_LOCALE
    base = locale.replace("-", "_").split("_")[0]
    return base if base in SUPPORTED_LOCALES else DEFAULT_LOCALE


def t(key: str, locale: str | None = None) -> str:
    locale = normalize_locale(locale)
    catalog = _CATALOGS.get(locale, {})
    if key in catalog:
        return catalog[key]
    if locale != DEFAULT_LOCALE and key in _CATALOGS[DEFAULT_LOCALE]:
        return _CATALOGS[DEFAULT_LOCALE][key]
    logging.warning("Missing translation key: %s (locale=%s)", key, locale)
    return key
