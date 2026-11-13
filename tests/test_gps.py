import os
import socket
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geofence import Geofence  # noqa: E402
from gps import GpsReceiver, local_offset_m, parse_packet  # noqa: E402


def test_parse_valid_packet():
    fix = parse_packet(b"-23.550520,-46.633308,760.2,8,1.10,1\n")
    assert fix.lat == pytest.approx(-23.55052)
    assert fix.satellites == 8 and fix.has_fix and fix.is_reliable


@pytest.mark.parametrize("bad", [
    b"", b"lixo", b"1,2,3", b"abc,2,3,4,5,1", b"91,0,0,5,1.0,1",
    b"0,181,0,5,1.0,1", b"0,0,0,5,1.0,2", b"nan,0,0,5,1.0,1", b"\xff\xfe,1,2,3,4,5",
])
def test_parse_rejects_malformed(bad):
    assert parse_packet(bad) is None


def test_no_fix_or_poor_quality_is_not_reliable():
    assert not parse_packet("0,0,0,2,99.99,0").is_reliable
    assert not parse_packet("-23.5,-46.6,10,3,1.0,1").is_reliable   # poucos satélites
    assert not parse_packet("-23.5,-46.6,10,8,9.0,1").is_reliable   # HDOP alto


def test_stale_detection():
    fix = parse_packet("-23.5,-46.6,10,8,1.0,1", received_at=100.0)
    assert fix.is_stale(now=110.0) and not fix.is_stale(now=101.0)


def test_local_offset_north_and_east():
    o = parse_packet("-23.5,-46.6,0,8,1.0,1")
    north = parse_packet("-23.499,-46.6,0,8,1.0,1")      # ~111 m ao norte
    east = parse_packet("-23.5,-46.599,0,8,1.0,1")       # ~102 m a leste
    e, n = local_offset_m(o, north)
    assert n == pytest.approx(111.2, rel=0.01) and abs(e) < 0.01
    e, n = local_offset_m(o, east)
    assert e == pytest.approx(102.0, rel=0.01) and abs(n) < 0.01


def test_geofence_check_distance():
    g = Geofence(500, 300)
    assert g.check(499, 100) is None
    assert "raio" in g.check(501, 100)
    assert "altura" in g.check(100, 301)


def test_receiver_gets_real_udp_packet():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    rx = GpsReceiver(port=port)
    rx.start()
    try:
        tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tx.sendto(b"junk", ("127.0.0.1", port))                       # ignorado
        tx.sendto(b"-23.5,-46.6,10.0,7,1.2,1\n", ("127.0.0.1", port))
        for _ in range(40):
            if rx.latest: break
            time.sleep(0.05)
        assert rx.latest is not None and rx.latest.satellites == 7
    finally:
        rx.stop()
