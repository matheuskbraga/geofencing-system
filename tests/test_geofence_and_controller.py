import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from drone_commands import (DroneConnectionError, DroneNotConnectedError,  # noqa: E402
                            GeofenceViolationError, InvalidMoveError, TelloController)
from geofence import Geofence, Position, haversine_m  # noqa: E402


class FakeTello:
    def __init__(self):
        self.calls = []

    def connect(self): self.calls.append("connect")
    def takeoff(self): self.calls.append("takeoff")
    def land(self): self.calls.append("land")
    def emergency(self): self.calls.append("emergency")
    def end(self): self.calls.append("end")
    def get_battery(self): return 87
    def get_height(self): return 80
    def move_forward(self, d): self.calls.append(("forward", d))
    def move_back(self, d): self.calls.append(("back", d))
    def move_left(self, d): self.calls.append(("left", d))
    def move_right(self, d): self.calls.append(("right", d))
    def move_up(self, d): self.calls.append(("up", d))
    def move_down(self, d): self.calls.append(("down", d))


@pytest.fixture
def ctrl():
    fake = FakeTello()
    c = TelloController(tello_factory=lambda: fake, geofence=Geofence(200, 150))
    c.fake = fake
    return c


@pytest.fixture
def flying(ctrl):
    ctrl.connect()
    ctrl.takeoff()
    return ctrl


# --- Geofence --------------------------------------------------------------------
def test_geofence_inside_and_outside():
    g = Geofence(radius_cm=100, max_height_cm=100)
    assert g.contains(Position(60, 80, 50))          # distância exata = 100
    assert not g.contains(Position(80, 80, 50))
    assert "altura" in g.violation(Position(0, 0, 101))


def test_geofence_disabled_allows_everything():
    assert Geofence(10, 10, enabled=False).contains(Position(9999, 9999, 9999))


def test_haversine_one_degree_latitude():
    assert haversine_m(0, 0, 1, 0) == pytest.approx(111_195, rel=1e-3)


# --- Controller ------------------------------------------------------------------
def test_commands_require_connection(ctrl):
    with pytest.raises(DroneNotConnectedError):
        ctrl.takeoff()


def test_connect_failure_wrapped():
    def boom():
        raise OSError("sem rede")
    with pytest.raises(DroneConnectionError):
        TelloController(tello_factory=boom).connect()


def test_back_button_really_moves_back(flying):
    flying.move("back", 60)
    assert flying.fake.calls[-1] == ("back", 60)     # bug original: chamava forward
    assert flying.position.y == -60


def test_move_requires_takeoff(ctrl):
    ctrl.connect()
    with pytest.raises(InvalidMoveError):
        ctrl.move("forward", 60)


def test_move_distance_limits(flying):
    for bad in (10, 501):
        with pytest.raises(InvalidMoveError):
            flying.move("forward", bad)


def test_geofence_blocks_move_before_sending_command(flying):
    flying.move("forward", 200)                       # dentro de raio 200
    n_calls = len(flying.fake.calls)
    with pytest.raises(GeofenceViolationError):
        flying.move("forward", 20)
    assert len(flying.fake.calls) == n_calls          # drone NÃO recebeu o comando
    assert len(flying.violations.events) == 1
    assert flying.position.y == 200                   # posição inalterada


def test_height_limit(flying):
    with pytest.raises(GeofenceViolationError):
        flying.move("up", 100)                        # 80 + 100 > 150


def test_land_and_emergency_reset_state(flying):
    flying.emergency()
    assert not flying.flying and flying.position.z == 0


def test_end_is_safe_without_connection():
    c = TelloController(tello_factory=FakeTello)
    c.end()
    assert not c.is_connected()


def test_telemetry(flying):
    assert flying.telemetry() == {"battery": 87, "height_cm": 80}
