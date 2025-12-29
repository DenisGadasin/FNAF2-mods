"""FNAF2 Mod: It's me

Drop this file into the game's Mods folder.
The base game is expected to load the module and call init_mod().

Behavior:
- Every 60 seconds shows "It's me" for 3 seconds.
- Draw position is random each time.

Implementation approach:
- Monkeypatch pygame.display.flip() so we can draw right before frame is presented.
- Uses game's global `screen`, `WIN_W`, `WIN_H` via __main__.

Safety:
- Best-effort and exception-safe (won't crash the game).
"""

from __future__ import annotations

import random
import time


_ORIGINAL_FLIP = None

# Timing (ms)
INTERVAL_MS = 60_000
DURATION_MS = 3_000

_state = {
    "next_show_ms": None,
    "hide_at_ms": None,
    "pos": (0, 0),
    "active": False,
}


def _get_ticks(game) -> int:
    try:
        return int(game.pygame.time.get_ticks())
    except Exception:
        # Fallback to wall time if needed
        return int(time.time() * 1000)


def _ensure_schedule(now_ms: int):
    if _state["next_show_ms"] is None:
        _state["next_show_ms"] = now_ms + INTERVAL_MS


def _maybe_update_state(game, now_ms: int):
    _ensure_schedule(now_ms)

    # If currently active and time passed -> hide
    if _state["active"] and _state["hide_at_ms"] is not None and now_ms >= _state["hide_at_ms"]:
        _state["active"] = False
        _state["hide_at_ms"] = None
        _state["next_show_ms"] = now_ms + INTERVAL_MS

    # If not active and it's time -> show
    if (not _state["active"]) and _state["next_show_ms"] is not None and now_ms >= _state["next_show_ms"]:
        win_w = int(getattr(game, "WIN_W", 1920))
        win_h = int(getattr(game, "WIN_H", 1080))

        # Random position with some padding
        x = random.randint(50, max(50, win_w - 350))
        y = random.randint(50, max(50, win_h - 120))

        _state["pos"] = (x, y)
        _state["active"] = True
        _state["hide_at_ms"] = now_ms + DURATION_MS


def _draw_overlay(game):
    if not _state["active"]:
        return

    screen = getattr(game, "screen", None)
    if screen is None:
        return

    # Use game's font if present; otherwise fallback.
    font = getattr(game, "font_main", None)
    if font is None:
        try:
            font = game.pygame.font.SysFont("Arial", 90, bold=True)
        except Exception:
            return

    text_surf = font.render("It's me", True, (255, 255, 255))

    # Simple shadow for readability
    shadow = font.render("It's me", True, (0, 0, 0))
    x, y = _state["pos"]
    screen.blit(shadow, (x + 4, y + 4))
    screen.blit(text_surf, (x, y))


def _patched_flip(*args, **kwargs):
    try:
        import __main__ as game  # type: ignore
        now_ms = _get_ticks(game)
        _maybe_update_state(game, now_ms)
        _draw_overlay(game)
    except Exception:
        pass

    return _ORIGINAL_FLIP(*args, **kwargs)


def init_mod():
    """Entry point called by the game when mod is launched."""
    global _ORIGINAL_FLIP

    try:
        import __main__ as game  # type: ignore
        pygame = game.pygame

        if _ORIGINAL_FLIP is None:
            _ORIGINAL_FLIP = pygame.display.flip
            pygame.display.flip = _patched_flip

        # Initialize schedule immediately
        _ensure_schedule(_get_ticks(game))
    except Exception:
        # If we can't patch, do nothing.
        return
