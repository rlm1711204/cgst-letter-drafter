"""Theme presets (data/themes.json) + user themes + per-letter overrides."""
from __future__ import annotations

import copy

from .config import load_data

BASE = "CBIC Classic"


def all_themes(user_themes: dict | None = None) -> dict:
    data = load_data("themes")
    themes = dict(data.get("themes", {}))
    themes.update(user_themes or {})
    return themes


def theme_names(user_themes: dict | None = None) -> list[str]:
    return list(all_themes(user_themes))


def resolve(name: str | None = None, overrides: dict | None = None, user_themes: dict | None = None,
            detected: dict | None = None) -> dict:
    """BASE <- preset <- detected-from-sample <- overrides. Labels merged key-wise."""
    data = load_data("themes")
    themes = all_themes(user_themes)
    theme = copy.deepcopy(themes.get(BASE, {}))
    layers = []
    if name and name in themes and name != BASE:
        layers.append(themes[name])
    if detected:
        layers.append(detected)
    if overrides:
        layers.append({k: v for k, v in overrides.items() if v not in (None, "", "(theme default)")})
    for layer in layers:
        for k, v in layer.items():
            if k == "labels" and isinstance(v, dict):
                theme.setdefault("labels", {}).update({a: b for a, b in v.items() if b})
            else:
                theme[k] = v
    if theme.get("bilingual_labels"):
        bi = data.get("bilingual_labels", {})
        theme.setdefault("labels", {}).update({k: v for k, v in bi.items() if k not in ("closing", "salutation")})
        theme["closing_override"] = bi.get("closing")
        theme["salutation_override"] = bi.get("salutation")
    return theme
