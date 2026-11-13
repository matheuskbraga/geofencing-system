"""Recepção dos dados de GPS enviados pelo ESP8266 (firmware/transmitter).

Protocolo: pacotes UDP de texto, uma linha por pacote:
    lat,lon,alt,sats,hdop,fix
Este módulo não depende de Tkinter nem do drone.
"""
from __future__ import annotations

import logging
import math
import socket
import threading
import time
from dataclasses import dataclass
from typing import Optional

from config import GPS_MAX_HDOP, GPS_MIN_SATELLITES, GPS_STALE_SECONDS, GPS_UDP_PORT
from geofence import EARTH_RADIUS_M

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class GpsFix:
    lat: float
    lon: float
    alt_m: float
    satellites: int
    hdop: float
    has_fix: bool
    received_at: float  # time.monotonic() de quando o pacote chegou

    @property
    def is_reliable(self) -> bool:
        """Tem fix e qualidade mínima (satélites e HDOP) para confiar na posição."""
        return (self.has_fix and self.satellites >= GPS_MIN_SATELLITES
                and self.hdop <= GPS_MAX_HDOP)

    def is_stale(self, now: Optional[float] = None) -> bool:
        return (now if now is not None else time.monotonic()) - self.received_at > GPS_STALE_SECONDS


def parse_packet(data: bytes | str, received_at: Optional[float] = None) -> Optional[GpsFix]:
    """Converte um pacote em GpsFix. Devolve None se estiver malformado
    (pacote truncado, lixo, valores fora de faixa) em vez de lançar exceção."""
    try:
        text = data.decode("ascii", errors="strict") if isinstance(data, bytes) else data
        parts = text.strip().split(",")
        if len(parts) != 6:
            return None
        lat, lon, alt, hdop = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[4])
        sats, fix = int(parts[3]), int(parts[5])
    except (ValueError, UnicodeDecodeError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180) or fix not in (0, 1) or sats < 0:
        return None
    if any(math.isnan(v) or math.isinf(v) for v in (lat, lon, alt, hdop)):
        return None
    return GpsFix(lat, lon, alt, sats, hdop, bool(fix),
                  received_at if received_at is not None else time.monotonic())


def local_offset_m(origin: GpsFix, fix: GpsFix) -> tuple[float, float]:
    """Deslocamento (leste, norte) em metros de `origin` até `fix`.

    Aproximação equirretangular: precisa em distâncias de dezenas/centenas de
    metros, que é a escala de um geofence de drone.
    """
    north = math.radians(fix.lat - origin.lat) * EARTH_RADIUS_M
    east = (math.radians(fix.lon - origin.lon) * EARTH_RADIUS_M
            * math.cos(math.radians(origin.lat)))
    return east, north


class GpsReceiver:
    """Escuta UDP numa thread e guarda o último pacote válido recebido."""

    def __init__(self, port: int = GPS_UDP_PORT):
        self.port = port
        self._latest: Optional[GpsFix] = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._sock: Optional[socket.socket] = None
        self.error: Optional[str] = None

    @property
    def latest(self) -> Optional[GpsFix]:
        with self._lock:
            return self._latest

    def start(self) -> None:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind(("0.0.0.0", self.port))
            self._sock.settimeout(0.5)  # acorda para checar o pedido de parada
        except OSError as exc:
            # Porta ocupada etc.: o app continua funcionando, só sem GPS.
            self.error = f"GPS indisponível (porta {self.port}): {exc}"
            log.error(self.error)
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                data, _addr = self._sock.recvfrom(256)
            except socket.timeout:
                continue
            except OSError:
                break
            fix = parse_packet(data)
            if fix is not None:
                with self._lock:
                    self._latest = fix

    def stop(self) -> None:
        self._stop.set()
        if self._sock is not None:
            self._sock.close()
