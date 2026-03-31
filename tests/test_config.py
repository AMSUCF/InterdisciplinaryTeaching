# tests/test_config.py
import os
import pytest
from canvas_sync.config import load_config, Config


def test_load_config_from_file(tmp_path):
    config_file = tmp_path / "canvas_config.yaml"
    config_file.write_text(
        "api_url: https://webcourses.ucf.edu\n"
        "api_key: test-key-123\n"
        "course_id: 99999\n"
    )
    cfg = load_config(str(config_file))
    assert cfg.api_url == "https://webcourses.ucf.edu"
    assert cfg.api_key == "test-key-123"
    assert cfg.course_id == 99999


def test_load_config_missing_field(tmp_path):
    config_file = tmp_path / "canvas_config.yaml"
    config_file.write_text("api_url: https://webcourses.ucf.edu\n")
    with pytest.raises(KeyError):
        load_config(str(config_file))


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/canvas_config.yaml")
