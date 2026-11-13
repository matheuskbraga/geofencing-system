"""Modo demonstração: drone e GPS simulados (python main.py --demo).

Permite experimentar a interface, o teclado e o geofence sem hardware.
"""
from __future__ import annotations

import math
import random
import time
from typing import Optional

from gps import GpsFix

SIM_ORIGIN = (-23.550520, -46.633308)   # ponto qualquer, só para a demo


class SimTello:
    """Imita o djitellopy: comandos demoram um pouco, como no drone real."""

    def __init__(self, delay_s: float = 0.35):
        self.delay_s = delay_s
        self.height = 0
        self.battery = 92

    def connect(self): time.sleep(0.4)

    def takeoff(self):
        time.sleep(1.0); self.height = 80; self.battery -= 1

    def land(self):
        time.sleep(1.0); self.height = 0

    def emergency(self): self.height = 0
    def end(self): pass
    def get_battery(self): return max(0, self.battery)
    def get_height(self): return self.height

    def _move(self):
        time.sleep(self.delay_s)
        if random.random() < 0.1:
            self.battery -= 1

    def move_forward(self, d): self._move()
    def move_back(self, d): self._move()
    def move_left(self, d): self._move()
    def move_right(self, d): self._move()
    def move_up(self, d): self._move(); self.height += d
    def move_down(self, d): self._move(); self.height = max(0, self.height - d)


class SimGps:
    """GPS falso: deriva da posição estimada do controlador, com ruído.

    Na demo o drone "olha para o norte": x = leste, y = norte.
    """
    error: Optional[str] = None

    def __init__(self, controller):
        self.controller = controller

    def start(self): pass
    def stop(self): pass

    @property
    def latest(self) -> GpsFix:
        p = self.controller.position
        east = p.x / 100 + random.gauss(0, 0.3)
        north = p.y / 100 + random.gauss(0, 0.3)
        lat0, lon0 = SIM_ORIGIN
        lat = lat0 + math.degrees(north / 6_371_000.0)
        lon = lon0 + math.degrees(east / (6_371_000.0 * math.cos(math.radians(lat0))))
        return GpsFix(lat, lon, 760.0, 9, 1.1, True, time.monotonic())
