# canvas_sync/config.py
from __future__ import annotations

from dataclasses import dataclass

import yaml

DEFAULT_SLIDES_BASE_URL = "https://anastasiasalter.net/InterdisciplinaryTeaching/slides/"


@dataclass
class Config:
    api_url: str
    api_key: str
    course_id: int
    course_start: str = ""
    slides_base_url: str = DEFAULT_SLIDES_BASE_URL


def load_config(path: str) -> Config:
    with open(path) as f:
        data = yaml.safe_load(f)
    return Config(
        api_url=data["api_url"],
        api_key=data["api_key"],
        course_id=data["course_id"],
        course_start=str(data.get("course_start", "")),
        slides_base_url=data.get("slides_base_url", DEFAULT_SLIDES_BASE_URL),
    )
