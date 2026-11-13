"""Constantes centrais do projeto.

Concentrar valores "mágicos" aqui evita repetição (antes o número 60 aparecia
em 6 botões) e facilita ajustar o comportamento sem mexer na lógica.
"""

# --- Limites do protocolo do Tello (centímetros) -----------------------------
MIN_MOVE_CM = 20
MAX_MOVE_CM = 500
DEFAULT_MOVE_CM = 60

# Altura aproximada que o Tello atinge ao decolar.
TAKEOFF_HEIGHT_CM = 80

# --- Geofence padrão (metros) --------------------------------------------------
DEFAULT_RADIUS_M = 5.0
DEFAULT_MAX_HEIGHT_M = 3.0

# --- GPS (ESP8266 + NEO-6M) ----------------------------------------------------
GPS_UDP_PORT = 5005          # mesma porta de PC_PORT em firmware/transmitter.ino
GPS_MIN_SATELLITES = 4       # abaixo disso a posição não é confiável
GPS_MAX_HDOP = 5.0           # HDOP alto = geometria ruim dos satélites
GPS_STALE_SECONDS = 3.0      # sem pacote há mais que isso = sinal perdido
GPS_CHECK_INTERVAL_MS = 500  # frequência de checagem do geofence por GPS

# --- Interface ---------------------------------------------------------------
WINDOW_TITLE = "Geofencing Lab"
WINDOW_WIDTH = 1366   # tamanho preferido; é reduzido se a tela for menor
WINDOW_HEIGHT = 800
TELEMETRY_INTERVAL_MS = 1500  # a cada quantos ms atualizar bateria/altura
UI_POLL_INTERVAL_MS = 100      # a cada quantos ms processar resultados das threads

MODE_FREE = "Voo livre"
MODE_FENCED = "Modo delimitação"
