import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from keyboard import KEYMAP, MOVES, Action, ConfirmGate, resolve  # noqa: E402


def test_wasd_and_arrows():
    assert resolve("w") is Action.FORWARD and resolve("s") is Action.BACK
    assert resolve("a") is Action.LEFT and resolve("d") is Action.RIGHT
    assert resolve("Up") is Action.UP and resolve("Down") is Action.DOWN


def test_case_insensitive_capslock():
    assert resolve("W") is Action.FORWARD and resolve("T") is Action.TAKEOFF


def test_unmapped_key_is_ignored():
    assert resolve("q") is None and resolve("F5") is None


def test_land_has_two_keys_and_all_moves_mapped():
    assert resolve("l") is Action.LAND and resolve("space") is Action.LAND
    assert MOVES <= set(KEYMAP.values())


def test_emergency_needs_double_press():
    g = ConfirmGate(window_s=1.5)
    assert g.confirm(10.0) is False        # 1º toque só arma
    assert g.confirm(10.8) is True         # 2º dentro da janela confirma
    assert g.confirm(11.0) is False        # depois de confirmar, rearma


def test_emergency_gate_expires():
    g = ConfirmGate(window_s=1.5)
    g.confirm(10.0)
    assert g.confirm(12.0) is False        # passou da janela: conta como novo 1º toque
