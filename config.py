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

# --- Interface ---------------------------------------------------------------
WINDOW_TITLE = "Software de Delimitação"
WINDOW_SIZE = "1280x720"
TELEMETRY_INTERVAL_MS = 2000   # a cada quantos ms atualizar bateria/altura
UI_POLL_INTERVAL_MS = 100      # a cada quantos ms processar resultados das threads

MODE_FREE = "Voo livre"
MODE_FENCED = "Modo delimitação"
