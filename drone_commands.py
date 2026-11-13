"""Camada de comunicação com o drone Tello.

O controlador:
  * valida conexão e parâmetros antes de enviar qualquer comando;
  * faz dead reckoning (estima a posição somando os movimentos enviados);
  * consulta o Geofence ANTES de mover, bloqueando movimentos que sairiam da área.
"""
from __future__ import annotations

import functools
import logging
from typing import Callable, Optional

from config import MAX_MOVE_CM, MIN_MOVE_CM, TAKEOFF_HEIGHT_CM
from geofence import Geofence, Position, ViolationEvent, ViolationLog

log = logging.getLogger(__name__)


# --- Exceções próprias: a UI consegue distinguir cada tipo de problema --------
class DroneError(Exception):
    """Base de todos os erros do drone."""


class DroneNotConnectedError(DroneError):
    pass


class DroneConnectionError(DroneError):
    pass


class InvalidMoveError(DroneError):
    pass


class GeofenceViolationError(DroneError):
    def __init__(self, event: ViolationEvent):
        super().__init__(event.reason)
        self.event = event


def requires_connection(func):
    """Bloqueia o método se o drone não estiver conectado."""
    @functools.wraps(func)  # preserva __name__ e docstring do método original
    def wrapper(self, *args, **kwargs):
        if not self.is_connected():
            raise DroneNotConnectedError(
                "Drone não está conectado. Clique em CONECTAR primeiro.")
        return func(self, *args, **kwargs)
    return wrapper


# direção -> (método do djitellopy, vetor unitário (dx, dy, dz))
_DIRECTIONS = {
    "forward": ("move_forward", (0, 1, 0)),
    "back":    ("move_back",    (0, -1, 0)),
    "right":   ("move_right",   (1, 0, 0)),
    "left":    ("move_left",    (-1, 0, 0)),
    "up":      ("move_up",      (0, 0, 1)),
    "down":    ("move_down",    (0, 0, -1)),
}


def _default_tello_factory():
    # Import tardio: permite testar o projeto sem o djitellopy instalado.
    from djitellopy import Tello
    return Tello()


class TelloController:
    def __init__(self, tello_factory: Callable = _default_tello_factory,
                 geofence: Optional[Geofence] = None):
        self._tello_factory = tello_factory
        self.tello = None
        self._connected = False
        self.geofence = geofence
        self.violations = ViolationLog()
        self.position = Position()
        self.flying = False

    # -- conexão ---------------------------------------------------------------
    def connect(self) -> None:
        try:
            self.tello = self._tello_factory()
            self.tello.connect()  # lança exceção se falhar
        except Exception as exc:
            self._connected = False
            raise DroneConnectionError(f"Falha ao conectar: {exc}") from exc
        self._connected = True
        self.position = Position()
        self.flying = False

    def is_connected(self) -> bool:
        return self._connected

    def end(self) -> None:
        """Encerra a conexão. Não exige estar conectado (limpeza segura)."""
        if self.tello is not None:
            try:
                self.tello.end()
            except Exception:
                log.exception("Erro ao encerrar o Tello")
        self._connected = False
        self.flying = False

    # -- voo -------------------------------------------------------------------
    @requires_connection
    def takeoff(self) -> None:
        self.tello.takeoff()
        self.flying = True
        self.position = Position(0, 0, TAKEOFF_HEIGHT_CM)

    @requires_connection
    def land(self) -> None:
        self.tello.land()
        self.flying = False
        self.position = Position(self.position.x, self.position.y, 0)

    @requires_connection
    def emergency(self) -> None:
        """Corta os motores imediatamente."""
        self.tello.emergency()
        self.flying = False
        self.position = Position(self.position.x, self.position.y, 0)

    @requires_connection
    def move(self, direction: str, distance_cm: int) -> None:
        if direction not in _DIRECTIONS:
            raise InvalidMoveError(f"Direção inválida: {direction}")
        if not self.flying:
            raise InvalidMoveError("O drone precisa decolar antes de se mover.")
        if not MIN_MOVE_CM <= distance_cm <= MAX_MOVE_CM:
            raise InvalidMoveError(
                f"Distância deve estar entre {MIN_MOVE_CM} e {MAX_MOVE_CM} cm.")

        method_name, (ux, uy, uz) = _DIRECTIONS[direction]
        target = self.position.moved(ux * distance_cm, uy * distance_cm, uz * distance_cm)

        # Geofence: checa o destino ANTES de enviar o comando ao drone.
        if self.geofence is not None:
            reason = self.geofence.violation(target)
            if reason:
                event = self.violations.record(target, reason)
                log.warning(str(event))
                raise GeofenceViolationError(event)

        getattr(self.tello, method_name)(distance_cm)
        self.position = target  # só atualiza se o comando não lançou erro

    # -- telemetria --------------------------------------------------------------
    @requires_connection
    def telemetry(self) -> dict:
        return {
            "battery": self.tello.get_battery(),
            "height_cm": self.tello.get_height(),
        }
