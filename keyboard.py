"""Ações de voo e mapa de teclas (lógica pura, sem Tkinter).

Manter o mapa aqui permite testar o teclado sem abrir janela e mudar
as teclas em um único lugar.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional


class Action(str, Enum):
    FORWARD = "forward"
    BACK = "back"
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"
    TAKEOFF = "takeoff"
    LAND = "land"
    EMERGENCY = "emergency"
    STEP_UP = "step_up"
    STEP_DOWN = "step_down"


MOVES = frozenset({Action.FORWARD, Action.BACK, Action.LEFT,
                   Action.RIGHT, Action.UP, Action.DOWN})

# Nomes de tecla do Tk (event.keysym), em minúsculas.
KEYMAP = {
    "w": Action.FORWARD, "s": Action.BACK, "a": Action.LEFT, "d": Action.RIGHT,
    "up": Action.UP, "r": Action.UP,
    "down": Action.DOWN, "f": Action.DOWN,
    "t": Action.TAKEOFF,
    "l": Action.LAND, "space": Action.LAND,
    "escape": Action.EMERGENCY,
    "plus": Action.STEP_UP, "equal": Action.STEP_UP, "kp_add": Action.STEP_UP,
    "minus": Action.STEP_DOWN, "kp_subtract": Action.STEP_DOWN,
}


def resolve(keysym: str) -> Optional[Action]:
    """Tecla -> ação (ignora maiúsculas/CapsLock). None se não mapeada."""
    return KEYMAP.get(keysym.lower())


class ConfirmGate:
    """Exige dois acionamentos seguidos dentro de `window_s` segundos.

    Usado na EMERGÊNCIA (que desliga os motores): um toque acidental
    em Esc não derruba o drone.
    """

    def __init__(self, window_s: float = 1.5):
        self.window_s = window_s
        self._armed_at: Optional[float] = None

    def confirm(self, now: float) -> bool:
        if self._armed_at is not None and now - self._armed_at <= self.window_s:
            self._armed_at = None
            return True
        self._armed_at = now
        return False
