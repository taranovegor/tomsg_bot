"""
Tests for Config.

getLevelName(None) produces "Level None" and crashes logging.basicConfig.
The fix adds a default of "INFO" to the LOG_LEVEL env-var lookup.
"""

import logging
import os
from importlib import reload
from unittest.mock import patch


class TestLogLevelDefault:
    def _load_config_without_log_level_env(self):
        env = {k: v for k, v in os.environ.items() if k != "LOG_LEVEL"}
        with patch.dict(os.environ, env, clear=True):
            import core.config as cfg_module

            reload(cfg_module)
            return cfg_module.Config()

    def test_defaults_to_info_when_env_var_absent(self):
        config = self._load_config_without_log_level_env()
        assert config.log_level == logging.INFO, (
            f"Expected logging.INFO (20), got {config.log_level!r}"
        )

    def test_never_produces_level_none_string(self):
        """'Level None' would crash logging.basicConfig with a ValueError."""
        config = self._load_config_without_log_level_env()
        assert config.log_level != "Level None"

    def test_honours_explicit_env_var(self):
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            import core.config as cfg_module

            reload(cfg_module)
            config = cfg_module.Config()

        assert config.log_level == logging.DEBUG
