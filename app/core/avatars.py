"""Avatar rules shared by the auth and profile flows.

A user picks an avatar from DiceBear during onboarding and we store its path,
for example ``dicebear/img/ryg5``. Until one is picked, profiles fall back to
the image bundled with the frontend at ``$lib/assets/avatar_default.png``.
"""

import re

DEFAULT_AVATAR = "$lib/assets/avatar_default.png"
DICEBEAR_PREFIX = "dicebear/img/"
DICEBEAR_AVATAR_PATTERN = r"^dicebear/img/[A-Za-z0-9_-]{1,64}$"

_DICEBEAR_RE = re.compile(DICEBEAR_AVATAR_PATTERN)


def is_dicebear_avatar(value: str | None) -> bool:
    return bool(value) and value.startswith(DICEBEAR_PREFIX)


def display_avatar(value: str | None) -> str:
    """What the frontend should render: the chosen DiceBear avatar or the bundled default."""
    return value if is_dicebear_avatar(value) else DEFAULT_AVATAR


def validate_avatar(value: str) -> str:
    value = value.strip()
    if not _DICEBEAR_RE.fullmatch(value):
        raise ValueError(f"Avatar must look like '{DICEBEAR_PREFIX}<seed>'")
    return value


def avatar_payload(value: str | None, selected: bool = False) -> dict:
    chosen = selected and is_dicebear_avatar(value)
    return {
        "avatar": display_avatar(value if chosen else None),
        "is_dicebear_avatar": chosen,
        "avatar_selected": chosen,
    }
