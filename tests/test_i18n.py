from platforms.telegram.i18n import DEFAULT_LOCALE, normalize_locale, t


class TestNormalizeLocale:
    def test_none_returns_default(self):
        assert normalize_locale(None) == DEFAULT_LOCALE

    def test_empty_returns_default(self):
        assert normalize_locale("") == DEFAULT_LOCALE

    def test_known_locale_passthrough(self):
        assert normalize_locale("ru") == "ru"
        assert normalize_locale("en") == "en"

    def test_region_code_normalizes_to_base(self):
        assert normalize_locale("en-US") == "en"
        assert normalize_locale("ru-RU") == "ru"

    def test_unknown_locale_falls_back_to_default(self):
        assert normalize_locale("fr") == DEFAULT_LOCALE
        assert normalize_locale("de") == DEFAULT_LOCALE


class TestTFunction:
    def test_ru_returns_russian(self):
        assert t("invalid_url_reply", "ru") == "Введённый текст не является корректным URL."

    def test_en_returns_english(self):
        assert t("invalid_url_reply", "en") == "The entered text is not a valid URL."

    def test_none_locale_uses_default_ru(self):
        assert t("invalid_url_reply", None) == "Введённый текст не является корректным URL."

    def test_unknown_locale_falls_back_to_default_ru(self):
        assert t("invalid_url_reply", "fr") == "Введённый текст не является корректным URL."

    def test_missing_key_returns_key_itself(self):
        assert t("nonexistent_key", "ru") == "nonexistent_key"
        assert t("nonexistent_key", "en") == "nonexistent_key"

    def test_all_ru_keys_have_values(self):
        from platforms.telegram.locales.ru import translations

        for key, value in translations.items():
            result = t(key, "ru")
            assert result == value, f"Key {key!r} expected {value!r}, got {result!r}"

    def test_all_en_keys_have_values(self):
        from platforms.telegram.locales.en import translations

        for key, value in translations.items():
            result = t(key, "en")
            assert result == value, f"Key {key!r} expected {value!r}, got {result!r}"

    def test_region_code_uses_base_locale(self):
        assert t("invalid_url_reply", "en-US") == "The entered text is not a valid URL."
