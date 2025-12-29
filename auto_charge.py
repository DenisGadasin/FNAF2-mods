"""FNAF2 Mod: Auto Charge Music Box

Drop this file into the game's Mods folder.
The base game is expected to load the module and call init_mod().

Behavior:
- Always keeps Puppet music box charge at 100.
- If Puppet already woke up, tries to push it back to Box with full charge.

Implementation notes:
- The original game runs as __main__. We import __main__ and mutate its globals.
- This mod is best-effort: it won't crash the game if some globals don't exist.
"""

from __future__ import annotations

import time
import threading


_STOP = False
_THREAD: threading.Thread | None = None


def _loop():
    # Small delay so the main script finishes creating globals.
    time.sleep(0.5)

    while not _STOP:
        try:
            import __main__ as game  # type: ignore

            puppet = getattr(game, "puppet", None)
            if puppet is not None:
                # Keep the music box charged.
                if hasattr(puppet, "charge"):
                    puppet.charge = 100.0

                # If Puppet has woken up, try to reset it to safe state.
                # In the base script, Puppet uses pos values: "Box", "Awake", "Office".
                if getattr(puppet, "pos", None) != "Box":
                    puppet.pos = "Box"

                # Ensure discharge timers don't immediately reduce charge.
                now_ticks = None
                try:
                    # pygame.time.get_ticks exists in the base game
                    now_ticks = game.pygame.time.get_ticks()  # type: ignore
                except Exception:
                    now_ticks = None

                if now_ticks is not None:
                    puppet.last_discharge = now_ticks
                    puppet.discharge_time = 0
        except Exception:
            # Never crash the game from a mod.
            pass

        time.sleep(0.2)


def init_mod():
    """Entry point called by the game when mod is launched."""
    global _THREAD
    if _THREAD and _THREAD.is_alive():
        return

    _THREAD = threading.Thread(target=_loop, name="auto_charge_mod", daemon=True)
    _THREAD.start()
