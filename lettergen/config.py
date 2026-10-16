"""Paths, persistent settings (office profile, chosen template, theme) and data loading."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
REPO_DIR = PKG_DIR.parent
DATA_DIR = REPO_DIR / "data"
PROMPTS_DIR = REPO_DIR / "prompts"
EXAMPLES_DIR = REPO_DIR / "examples"
TEMPLATES_DIR = REPO_DIR / "templates"

DRIVE_ROOT = Path("/content/drive/MyDrive/CGST_Letter_Drafter")
LOCAL_ROOT = Path(os.environ.get("LETTERGEN_HOME", "/content/CGST_Letter_Drafter"
                                  if Path("/content").exists() else Path.home() / "CGST_Letter_Drafter"))

DEFAULT_PROFILE = {
    "office_lines": [
        "भारत सरकार / GOVERNMENT OF INDIA",
        "वित्त मंत्रालय, राजस्व विभाग / MINISTRY OF FINANCE, DEPARTMENT OF REVENUE",
        "OFFICE OF THE COMMISSIONER OF CGST & CENTRAL EXCISE",
        "TIRUNELVELI COMMISSIONERATE",
    ],
    "office_address": "[Office address - edit in Step 2]",
    "office_contact": "Phone: [ ]  |  Email: [ ]",
    "section": "Legal Section",
    "file_no_prefix": "",
    "signatory_name": "",
    "signatory_designation": "",
    "signatory_office_line": "",
    "home_state_code": "33",
    "place": "Tirunelveli",
}


def _read_json(path: Path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return copy.deepcopy(default)


def load_data(name: str) -> dict:
    """Load a JSON file from data/ (re-read each time so edits apply without restart)."""
    return _read_json(DATA_DIR / f"{name}.json", {})


class Workspace:
    """Folder (Google Drive or local) that keeps profile, templates, outputs and the register."""

    def __init__(self, root: Path | str | None = None):
        if root is None:
            root = DRIVE_ROOT if DRIVE_ROOT.parent.exists() else LOCAL_ROOT
        self.root = Path(root)
        for sub in ("templates", "outputs", "themes"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)

    # ---- generic settings -------------------------------------------------
    @property
    def settings_path(self) -> Path:
        return self.root / "settings.json"

    def settings(self) -> dict:
        return _read_json(self.settings_path, {})

    def save_settings(self, **kw) -> dict:
        s = self.settings()
        s.update(kw)
        self.settings_path.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
        return s

    # ---- office profile -----------------------------------------------------
    def profile(self) -> dict:
        p = copy.deepcopy(DEFAULT_PROFILE)
        p.update(_read_json(self.root / "profile.json", {}) or {})
        return p

    def save_profile(self, profile: dict) -> None:
        (self.root / "profile.json").write_text(json.dumps(profile, indent=2, ensure_ascii=False),
                                                encoding="utf-8")

    # ---- user themes ----------------------------------------------------------
    def user_themes(self) -> dict:
        return _read_json(self.root / "themes" / "my_themes.json", {}) or {}

    def save_user_theme(self, name: str, theme: dict) -> None:
        t = self.user_themes()
        t[name] = theme
        (self.root / "themes" / "my_themes.json").write_text(
            json.dumps(t, indent=2, ensure_ascii=False), encoding="utf-8")

    @property
    def outputs(self) -> Path:
        return self.root / "outputs"

    @property
    def templates(self) -> Path:
        return self.root / "templates"
