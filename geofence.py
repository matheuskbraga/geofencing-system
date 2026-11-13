"""Lógica pura de geofencing (sem interface e sem drone).

Por ser independente de Tkinter e djitellopy, este módulo é totalmente
testável com pytest.

Sistema de coordenadas local (em centímetros), com origem no ponto de
decolagem:
    x -> direita (+) / esquerda (-)
    y -> frente  (+) / trás     (-)
    z -> altura acima do solo
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

EARTH_RADIUS_M = 6_371_000.0


@dataclass(frozen=True)
class Position:
    """Posição relativa ao ponto de decolagem, em centímetros."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def moved(self, dx: float = 0, dy: float = 0, dz: float = 0) -> "Position":
        # frozen=True => imutável; "mover" devolve uma nova posição.
        return Position(self.x + dx, self.y + dy, self.z + dz)

    @property
    def horizontal_distance_cm(self) -> float:
        return math.hypot(self.x, self.y)


@dataclass
class Geofence:
    """Cilindro virtual: raio horizontal + altura máxima (ambos em cm)."""
    radius_cm: float
    max_height_cm: float
    enabled: bool = True

    def violation(self, pos: Position) -> Optional[str]:
        """Retorna o motivo da violação, ou None se a posição é permitida."""
        return self.check(pos.horizontal_distance_cm, pos.z)

    def check(self, horizontal_cm: float, height_cm: float) -> Optional[str]:
        """Mesma regra de `violation`, a partir de distância e altura já calculadas
        (usado pelo GPS, onde a distância vem de coordenadas, não de x/y)."""
        if not self.enabled:
            return None
        if horizontal_cm > self.radius_cm:
            return (f"fora do raio: {horizontal_cm / 100:.2f} m "
                    f"> {self.radius_cm / 100:.2f} m")
        if height_cm > self.max_height_cm:
            return (f"acima da altura máxima: {height_cm / 100:.2f} m "
                    f"> {self.max_height_cm / 100:.2f} m")
        if height_cm < 0:
            return f"abaixo do solo: {height_cm / 100:.2f} m"
        return None

    def contains(self, pos: Position) -> bool:
        return self.violation(pos) is None


@dataclass(frozen=True)
class ViolationEvent:
    timestamp: datetime
    attempted: Position
    reason: str

    def __str__(self) -> str:
        p = self.attempted
        return (f"[{self.timestamp:%H:%M:%S}] Violação ({self.reason}) "
                f"em x={p.x:.0f} y={p.y:.0f} z={p.z:.0f} cm")


@dataclass
class ViolationLog:
    """Histórico em memória das violações (a UI lê daqui)."""
    events: list[ViolationEvent] = field(default_factory=list)

    def record(self, attempted: Position, reason: str) -> ViolationEvent:
        event = ViolationEvent(datetime.now(), attempted, reason)
        self.events.append(event)
        return event


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância em metros entre duas coordenadas GPS (fórmula de Haversine).

    Ainda não é usada pela UI: fica pronta para quando o módulo GNSS/ESP8266
    passar a enviar latitude/longitude reais.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))
