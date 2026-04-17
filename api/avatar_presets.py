"""Preset avatar catalog utilities."""

from typing import Any, Dict, List, Optional, Sequence

from django.conf import settings


DEFAULT_PRESET_AVATAR_OPTIONS: Sequence[Dict[str, str]] = (
    {
        "id": "avatar-01",
        "name": "Explorer One",
        "url": "https://api.dicebear.com/9.x/adventurer/svg?seed=Milo",
    },
    {
        "id": "avatar-02",
        "name": "Explorer Two",
        "url": "https://api.dicebear.com/9.x/adventurer/svg?seed=Ruby",
    },
    {
        "id": "avatar-03",
        "name": "Explorer Three",
        "url": "https://api.dicebear.com/9.x/adventurer/svg?seed=Kai",
    },
    {
        "id": "avatar-04",
        "name": "Explorer Four",
        "url": "https://api.dicebear.com/9.x/adventurer/svg?seed=Nova",
    },
    {
        "id": "avatar-05",
        "name": "Explorer Five",
        "url": "https://api.dicebear.com/9.x/adventurer/svg?seed=Atlas",
    },
    {
        "id": "avatar-06",
        "name": "Explorer Six",
        "url": "https://api.dicebear.com/9.x/adventurer/svg?seed=Ivy",
    },
    {
        "id": "avatar-07",
        "name": "Explorer Seven",
        "url": "https://api.dicebear.com/9.x/adventurer/svg?seed=Orion",
    },
    {
        "id": "avatar-08",
        "name": "Explorer Eight",
        "url": "https://api.dicebear.com/9.x/adventurer/svg?seed=Luna",
    },
)


def _coerce_option(value: Any, index: int) -> Optional[Dict[str, str]]:
    if not isinstance(value, dict):
        return None

    url = str(value.get("url", "")).strip()
    if not url:
        return None

    avatar_id = str(value.get("id") or f"avatar-{index + 1:02d}").strip()
    name = str(value.get("name") or avatar_id).strip()
    return {"id": avatar_id, "name": name, "url": url}


def get_avatar_presets() -> List[Dict[str, str]]:
    """
    Return fixed avatar options.

    Can be overridden by settings.PRESET_AVATAR_OPTIONS.
    """
    configured = getattr(settings, "PRESET_AVATAR_OPTIONS", None)
    if not configured:
        return list(DEFAULT_PRESET_AVATAR_OPTIONS)

    normalized: List[Dict[str, str]] = []
    for idx, item in enumerate(configured):
        coerced = _coerce_option(item, idx)
        if coerced:
            normalized.append(coerced)

    return normalized or list(DEFAULT_PRESET_AVATAR_OPTIONS)


def get_allowed_avatar_urls() -> set[str]:
    return {item["url"] for item in get_avatar_presets()}

