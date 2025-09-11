from pathlib import Path

import pytest
from pydantic import ValidationError

from signalai.config import load_settings


def test_load_settings(tmp_path):
    sample = Path(__file__).parent.parent / "signalai" / "config.toml"
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(sample.read_text())

    settings = load_settings(cfg_path)
    assert settings.style.wrap_col == 100
    assert settings.formatter.model == "gpt-5-mini"


def test_load_settings_validation(tmp_path):
    bad_cfg = tmp_path / "config.toml"
    bad_cfg.write_text(
        """
[style]
wrap_col = "wide"

[formatter]
model = "gpt"
"""
    )
    with pytest.raises(ValidationError):
        load_settings(bad_cfg)
