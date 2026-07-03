import os
import json
from pathlib import Path
from typing import Dict, Optional

from backend.excel_service.config import WorkbookTemplateConfig

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


class TemplateRegistry:
    """
    Resolves the active WorkbookTemplateConfig from a JSON profile file.

    Switching from the local demo templates to a real turnkey business's live
    workbook is a one-line config change: set the `EXCEL_TEMPLATE_PROFILE` env
    var to the name of a new JSON file dropped into `templates/` (e.g.
    `EXCEL_TEMPLATE_PROFILE=acme_corp` -> `templates/acme_corp.json`).
    """

    _cache: Dict[str, WorkbookTemplateConfig] = {}

    @classmethod
    def active_profile_name(cls) -> str:
        return os.getenv("EXCEL_TEMPLATE_PROFILE", "demo")

    @classmethod
    def load(cls, profile: Optional[str] = None) -> WorkbookTemplateConfig:
        profile = profile or cls.active_profile_name()
        if profile in cls._cache:
            return cls._cache[profile]

        config_path = TEMPLATES_DIR / f"{profile}.json"
        if not config_path.exists():
            raise FileNotFoundError(
                f"No Excel template configuration profile found at {config_path}. "
                f"Available profiles: {[p.stem for p in TEMPLATES_DIR.glob('*.json')]}"
            )

        with open(config_path, "r") as f:
            raw = json.load(f)

        config = WorkbookTemplateConfig(**raw)
        cls._cache[profile] = config
        return config

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()
