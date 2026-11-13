"""Interface gráfica (CustomTkinter), estilo educacional.

Estrutura da tela:
    HeaderBar     -> título, mensagem atual, estado e botão CONECTAR
    SensorPanel   -> monitores (bateria, altura, distância, GPS, posição, violações)
    ConfigPanel   -> modo, passo, raio, altura máxima, origem do GPS
    RadarPanel    -> vista de cima com geofence, trilha e medidor de altura
    ControlPanel  -> teclas de voo (clicáveis e acendem com o teclado)
    LogPanel      -> registro de eventos

Regra de ouro do Tkinter: só a thread principal mexe nos widgets. Comandos ao
drone bloqueiam, então rodam numa thread de trabalho e devolvem o resultado
por uma fila, lida pela thread principal via `after()`.
"""
from __future__ import annotations

import math
import queue
import threading
import time
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Callable, Optional

import customtkinter as ctk

import config
import theme as T
from drone_commands import DroneError, GeofenceViolationError, TelloController
from geofence import Geofence, Position
from gps import GpsFix, GpsReceiver, local_offset_m
from keyboard import MOVES, Action, ConfirmGate, resolve
from widgets import Card, HeightGauge, KeyCap, RadarCanvas, SensorTile


# ====================================================================== cabeçalho
class HeaderBar(ctk.CTkFrame):
    def __init__(self, master, app: "App"):
        super().__init__(master, fg_color=T.CARD, corner_radius=T.RADIUS,
                         border_width=1, border_color=T.BORDER)
        self.app = app
        self.columnconfigure(2, weight=1)

        ctk.CTkLabel(self, text="G", width=40, height=40, corner_radius=12, fg_color=T.PRIMARY,
                     text_color="white", font=T.font(22, "bold")).grid(row=0, column=0, padx=(14, 10), pady=10)
        title = ctk.CTkFrame(self, fg_color="transparent")
        title.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(title, text="Geofencing Lab", font=T.font(18, "bold"),
                     text_color=T.INK).pack(anchor="w")
        ctk.CTkLabel(title, text="Voo com cerca virtual", font=T.font(11),
                     text_color=T.MUTED).pack(anchor="w")

        self.banner = ctk.CTkFrame(self, fg_color=T.INFO_BG, corner_radius=12, height=40)
        self.banner.grid(row=0, column=2, sticky="ew", padx=16)
        self.banner.grid_propagate(False)
        self.msg = ctk.CTkLabel(self.banner, text="", font=T.font(13), text_color=T.INK,
                                anchor="w", justify="left")
        self.msg.pack(fill="x", padx=14, pady=8)

        self.conn = self._pill(3)
        self.flight = self._pill(4)
        self.mode = self._pill(5)
        self.button = ctk.CTkButton(self, text="CONECTAR", width=120, height=36, corner_radius=12,
                                    font=T.font(13, "bold"), fg_color=T.PRIMARY,
                                    hover_color=T.PRIMARY_HOVER, command=app.connect)
        self.button.grid(row=0, column=6, padx=(6, 14))

    def _pill(self, col: int) -> ctk.CTkLabel:
        pill = ctk.CTkLabel(self, text="", width=118, height=28, corner_radius=14,
                            font=T.font(12, "bold"))
        pill.grid(row=0, column=col, padx=4)
        return pill

    def set_message(self, text: str, kind: str = "info") -> None:
        bg, fg = {"error": (T.ERROR_BG, T.DANGER), "ok": (T.OK_BG, T.OK)}.get(kind, (T.INFO_BG, T.INK))
        self.banner.configure(fg_color=bg)
        self.msg.configure(text=text, text_color=fg)

    def refresh(self) -> None:
        c = self.app.controller
        if c.is_connected():
            self.conn.configure(text="● Conectado", fg_color=T.OK_BG, text_color=T.OK)
        else:
            self.conn.configure(text="● Desconectado", fg_color=T.ERROR_BG, text_color=T.DANGER)
        if c.flying:
            self.flight.configure(text="▲ Em voo", fg_color=T.INFO_BG, text_color=T.PRIMARY)
        else:
            self.flight.configure(text="■ No solo", fg_color=T.TILE, text_color=T.MUTED)
        if self.app.fence_active():
            self.mode.configure(text="⬡ Delimitação", fg_color="#DDF4F3", text_color="#0C8C89")
        else:
            self.mode.configure(text="Voo livre", fg_color=T.TILE, text_color=T.MUTED)
        self.button.configure(state="disabled" if self.app.busy or c.is_connected() else "normal")


# ====================================================================== sensores
class SensorPanel(Card):
    def __init__(self, master, app: "App"):
        super().__init__(master, "Monitor do drone", accent=T.TEAL)
        self.app = app
        for col in (0, 1):
            self.body.columnconfigure(col, weight=1, uniform="tiles")
        self.battery = SensorTile(self.body, "Bateria")
        self.height = SensorTile(self.body, "Altura")
        self.distance = SensorTile(self.body, "Distância da origem")
        self.gps = SensorTile(self.body, "GPS", with_bar=False)
        self.position = SensorTile(self.body, "Posição (cm)", with_bar=False)
        self.violations = SensorTile(self.body, "Violações", with_bar=False)
        tiles = (self.battery, self.height, self.distance, self.gps, self.position, self.violations)
        for i, tile in enumerate(tiles):
            tile.grid(row=i // 2, column=i % 2, sticky="nsew", padx=4, pady=4)

    def refresh(self) -> None:
        a, c = self.app, self.app.controller
        fence = c.geofence if a.fence_active() else None

        if a.battery is None:
            self.battery.set("--", "sem leitura", 0)
        else:
            self.battery.set(f"{a.battery}%", "", a.battery / 100, T.level_color(a.battery / 100, True))

        h = a.height_cm()
        if fence:
            ratio = h / fence.max_height_cm
            self.height.set(f"{h / 100:.2f} m", f"limite {fence.max_height_cm / 100:g} m",
                            ratio, T.level_color(ratio))
        else:
            self.height.set(f"{h / 100:.2f} m", "sem limite", h / 300, T.PRIMARY)

        d = c.position.horizontal_distance_cm / 100
        if fence:
            ratio = d / (fence.radius_cm / 100)
            self.distance.set(f"{d:.1f} m", f"raio {fence.radius_cm / 100:g} m",
                              ratio, T.level_color(ratio))
        else:
            self.distance.set(f"{d:.1f} m", "sem cerca", 0, T.PRIMARY)

        value, sub, color = a.gps_summary
        self.gps.set(value, sub, color=color)
        p = c.position
        self.position.set(f"{p.x:.0f}, {p.y:.0f}", "x lado · y frente")
        n = len(c.violations.events)
        self.violations.set(str(n), "nenhuma" if n == 0 else "tentativas bloqueadas",
                            color=T.DANGER if n else T.PRIMARY)


# ====================================================================== configuração
class ConfigPanel(Card):
    def __init__(self, master, app: "App"):
        super().__init__(master, "Configuração", accent=T.PURPLE)
        self.app = app
        b = self.body
        b.columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(b, text="Modo de operação", font=T.font(11), text_color=T.MUTED).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=4)
        self.mode = ctk.CTkComboBox(
            b, values=[config.MODE_FREE, config.MODE_FENCED], state="readonly", height=32,
            fg_color=T.TILE, border_color=T.BORDER, button_color=T.PRIMARY,
            command=lambda _v: self.apply())
        self.mode.set(config.MODE_FREE)
        self.mode.grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 8))

        self.step_label = ctk.CTkLabel(b, font=T.font(11), text_color=T.MUTED)
        self.step_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=4)
        self.step = ctk.CTkSlider(
            b, from_=config.MIN_MOVE_CM, to=config.MAX_MOVE_CM,
            number_of_steps=(config.MAX_MOVE_CM - config.MIN_MOVE_CM) // 10,
            button_color=T.PRIMARY, progress_color=T.PRIMARY, command=self._on_step)
        self.step.set(config.DEFAULT_MOVE_CM)
        self.step.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 8))
        self._on_step(config.DEFAULT_MOVE_CM)

        ctk.CTkLabel(b, text="Raio (m)", font=T.font(11), text_color=T.MUTED).grid(
            row=4, column=0, sticky="w", padx=4)
        ctk.CTkLabel(b, text="Altura máx. (m)", font=T.font(11), text_color=T.MUTED).grid(
            row=4, column=1, sticky="w", padx=4)
        self.radius = ctk.CTkEntry(b, height=32, fg_color=T.TILE, border_color=T.BORDER)
        self.radius.insert(0, str(config.DEFAULT_RADIUS_M))
        self.radius.grid(row=5, column=0, sticky="ew", padx=4, pady=(0, 8))
        self.height = ctk.CTkEntry(b, height=32, fg_color=T.TILE, border_color=T.BORDER)
        self.height.insert(0, str(config.DEFAULT_MAX_HEIGHT_M))
        self.height.grid(row=5, column=1, sticky="ew", padx=4, pady=(0, 8))
        for entry in (self.radius, self.height):
            entry.bind("<Return>", lambda _e: self.apply())

        self.auto_land = ctk.CTkCheckBox(b, text="Pousar ao violar (GPS)", font=T.font(12),
                                         text_color=T.INK, fg_color=T.PRIMARY,
                                         checkbox_width=20, checkbox_height=20)
        self.auto_land.grid(row=6, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 8))

        ctk.CTkButton(b, text="APLICAR", height=34, corner_radius=10, font=T.font(12, "bold"),
                      fg_color=T.PRIMARY, hover_color=T.PRIMARY_HOVER, command=self.apply).grid(
            row=7, column=0, sticky="ew", padx=4)
        ctk.CTkButton(b, text="ORIGEM GPS", height=34, corner_radius=10, font=T.font(12, "bold"),
                      fg_color=T.TILE, text_color=T.INK, hover_color=T.BORDER, border_width=1,
                      border_color=T.BORDER, command=app.set_gps_origin).grid(
            row=7, column=1, sticky="ew", padx=4)

    @property
    def auto_land_enabled(self) -> bool:
        return bool(self.auto_land.get())

    @property
    def step_cm(self) -> int:
        return int(round(self.step.get() / 10) * 10)

    def _on_step(self, value) -> None:
        self.step_label.configure(
            text=f"Distância por movimento: {int(round(float(value) / 10) * 10)} cm")

    def adjust_step(self, delta_cm: int) -> None:
        new = min(config.MAX_MOVE_CM, max(config.MIN_MOVE_CM, self.step_cm + delta_cm))
        self.step.set(new)
        self._on_step(new)

    def apply(self) -> None:
        """Lê os campos, valida e instala (ou remove) o geofence no controlador."""
        if self.mode.get() == config.MODE_FREE:
            self.app.controller.geofence = None
            self.app.notify("Voo livre: a cerca virtual está desativada.")
        else:
            try:
                radius_m = float(self.radius.get().replace(",", "."))
                height_m = float(self.height.get().replace(",", "."))
                if radius_m <= 0 or height_m <= 0:
                    raise ValueError
            except ValueError:
                self.app.notify("Raio e altura devem ser números maiores que zero.", "error")
                return
            self.app.controller.geofence = Geofence(radius_m * 100, height_m * 100)
            self.app.notify(f"Cerca ativa: raio {radius_m:g} m, altura máxima {height_m:g} m.", "ok")
        self.app.focus_set()           # devolve o foco ao teclado de voo
        self.app.refresh()


# ====================================================================== radar
class RadarPanel(Card):
    def __init__(self, master, app: "App"):
        super().__init__(master, "Radar de posição", accent=T.PRIMARY,
                         subtitle="vista de cima · posição estimada pelos comandos")
        self.app = app
        self.body.columnconfigure(0, weight=1)
        self.body.rowconfigure(0, weight=1)
        self.radar = RadarCanvas(self.body)
        self.radar.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.gauge = HeightGauge(self.body)
        self.gauge.grid(row=0, column=1, sticky="ns")

    def refresh(self) -> None:
        a, c = self.app, self.app.controller
        fence = c.geofence if a.fence_active() else None
        state = "violation" if a.recent_violation() else ("flying" if c.flying else "idle")
        self.radar.render(c.position, a.trail, fence, state)
        self.gauge.render(a.height_cm(), fence)


# ====================================================================== controles
class ControlPanel(Card):
    def __init__(self, master, app: "App"):
        super().__init__(master, "Controles de voo", accent=T.ACCENT,
                         subtitle="clique ou use o teclado")
        self.app = app
        self.keys: dict[Action, KeyCap] = {}
        b = self.body
        b.columnconfigure((0, 1), weight=1)

        move = ctk.CTkFrame(b, fg_color="transparent")
        move.grid(row=0, column=0, padx=6, pady=(4, 8))
        ctk.CTkLabel(move, text="MOVER", font=T.font(10, "bold"), text_color=T.MUTED).grid(
            row=0, column=0, columnspan=3, sticky="w")
        self._key(move, Action.FORWARD, "W", "Frente", 1, 1)
        self._key(move, Action.LEFT, "A", "Esquerda", 2, 0)
        self._key(move, Action.BACK, "S", "Trás", 2, 1)
        self._key(move, Action.RIGHT, "D", "Direita", 2, 2)

        alt = ctk.CTkFrame(b, fg_color="transparent")
        alt.grid(row=0, column=1, padx=6, pady=(4, 8))
        ctk.CTkLabel(alt, text="ALTITUDE", font=T.font(10, "bold"), text_color=T.MUTED).grid(
            row=0, column=0, sticky="w")
        self._key(alt, Action.UP, "↑", "Subir", 1, 0)
        self._key(alt, Action.DOWN, "↓", "Descer", 2, 0)

        flight = ctk.CTkFrame(b, fg_color="transparent")
        flight.grid(row=1, column=0, columnspan=2, pady=(4, 8))
        ctk.CTkLabel(flight, text="VOO", font=T.font(10, "bold"), text_color=T.MUTED).grid(
            row=0, column=0, columnspan=3, sticky="w")
        self._key(flight, Action.TAKEOFF, "T", "Decolar", 1, 0)
        self._key(flight, Action.LAND, "L", "Pousar (L/Espaço)", 1, 1, width=54)
        self._key(flight, Action.EMERGENCY, "Esc", "Emergência (2×)", 1, 2, width=64, danger=True)

        step = ctk.CTkFrame(b, fg_color="transparent")
        step.grid(row=2, column=0, columnspan=2, pady=(0, 4))
        ctk.CTkLabel(step, text="PASSO", font=T.font(10, "bold"), text_color=T.MUTED).grid(
            row=0, column=0, columnspan=2, sticky="w")
        self._key(step, Action.STEP_DOWN, "−", "Menor", 1, 0, width=44)
        self._key(step, Action.STEP_UP, "+", "Maior", 1, 1, width=44)

    def _key(self, parent, action: Action, text: str, caption: str, row: int, col: int,
             width: int = 54, danger: bool = False) -> None:
        cap = KeyCap(parent, text, caption, lambda a=action: self.app.perform(a, from_mouse=True),
                     width=width, danger=danger)
        cap.grid(row=row, column=col, padx=5, pady=2)
        self.keys[action] = cap

    def press(self, action: Action, pressed: bool) -> None:
        if action in self.keys:
            self.keys[action].press(pressed)

    def refresh(self) -> None:
        c, busy = self.app.controller, self.app.busy
        connected = c.is_connected()
        for action, cap in self.keys.items():
            if action in MOVES:
                cap.set_enabled(connected and c.flying and not busy)
            elif action == Action.TAKEOFF:
                cap.set_enabled(connected and not c.flying and not busy)
            elif action in (Action.LAND, Action.EMERGENCY):
                cap.set_enabled(connected)
            else:
                cap.set_enabled(True)


# ====================================================================== registro
class LogPanel(Card):
    def __init__(self, master):
        super().__init__(master, "Registro de eventos", accent=T.OK)
        self.box = ctk.CTkTextbox(self.body, state="disabled", fg_color=T.TILE, text_color=T.INK,
                                  font=T.font(12), corner_radius=12, wrap="word", height=220)
        self.box.pack(fill="both", expand=True)
        for tag, color in (("error", T.DANGER), ("ok", T.OK), ("info", T.INK), ("time", T.MUTED)):
            self.box.tag_config(tag, foreground=color)
        self._last: tuple[str, float] = ("", 0.0)

    def add(self, text: str, kind: str = "info") -> None:
        now = time.monotonic()
        if text == self._last[0] and now - self._last[1] < 1.5:
            return                      # evita inundar o registro com a mesma mensagem
        self._last = (text, now)
        self.box.configure(state="normal")
        self.box.insert("end", f"{datetime.now():%H:%M:%S}  ", "time")
        self.box.insert("end", text + "\n", kind)
        self.box.see("end")
        self.box.configure(state="disabled")


# ====================================================================== aplicação
class App(ctk.CTk):
    def __init__(self, controller: Optional[TelloController] = None, gps=None):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.title(config.WINDOW_TITLE)
        self._fit_to_screen()
        self.configure(fg_color=T.BG)

        self.controller = controller or TelloController()
        self.busy = 0                                       # nº de comandos em andamento
        self._executor = ThreadPoolExecutor(max_workers=1)  # serializa comandos
        self._results: queue.Queue = queue.Queue()          # threads -> UI
        self._emergency_gate = ConfirmGate()

        self.battery: Optional[int] = None
        self.trail: list[Position] = []
        self.gps = gps or GpsReceiver()
        self.gps.start()
        self.gps_origin: Optional[GpsFix] = None
        self.gps_summary = ("--", "aguardando ESP", T.PRIMARY)
        self._gps_violating = False

        self.columnconfigure(0, weight=0, minsize=345)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0, minsize=385)
        self.rowconfigure(1, weight=1)

        self.header = HeaderBar(self, self)
        self.header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=14, pady=(14, 8))

        left = ctk.CTkScrollableFrame(self, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=(0, 10))
        left.columnconfigure(0, weight=1)
        self.sensor_panel = SensorPanel(left, self)
        self.sensor_panel.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.config_panel = ConfigPanel(left, self)
        self.config_panel.grid(row=1, column=0, sticky="ew")

        self.radar_panel = RadarPanel(self, self)
        self.radar_panel.grid(row=1, column=1, sticky="nsew", padx=7, pady=(0, 14))

        right = ctk.CTkScrollableFrame(self, fg_color="transparent")
        right.grid(row=1, column=2, sticky="nsew", padx=(0, 8), pady=(0, 10))
        right.columnconfigure(0, weight=1)
        self.control_panel = ControlPanel(right, self)
        self.control_panel.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.log_panel = LogPanel(right)
        self.log_panel.grid(row=1, column=0, sticky="ew")

        # Teclado: bind_all vale para a janela inteira, qualquer widget com foco.
        self.bind_all("<KeyPress>", self._on_key_press)
        self.bind_all("<KeyRelease>", self._on_key_release)
        self.bind_all("<Button-1>", self._on_click)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.notify("Bem-vindo! Clique em CONECTAR para começar.")
        self.log_panel.add("Dica: W A S D movem · ↑ ↓ sobem/descem · T decola · L ou Espaço pousa "
                           "· Esc duas vezes = emergência.")
        self.refresh()
        self.after(config.UI_POLL_INTERVAL_MS, self._poll_results)
        self.after(config.TELEMETRY_INTERVAL_MS, self._poll_telemetry)
        self.after(config.GPS_CHECK_INTERVAL_MS, self._poll_gps)
        self.focus_set()

    def _fit_to_screen(self) -> None:
        """Limita a janela à área útil da tela (considera a escala/DPI do Windows)."""
        scale = ctk.ScalingTracker.get_window_scaling(self)
        avail_w = int(self.winfo_screenwidth() / scale) - 30
        avail_h = int(self.winfo_screenheight() / scale) - 110   # barra de tarefas + título
        w, h = min(config.WINDOW_WIDTH, avail_w), min(config.WINDOW_HEIGHT, avail_h)
        self.geometry(f"{w}x{h}+10+10")
        self.minsize(min(1000, w), min(560, h))

    # -- estado derivado ------------------------------------------------------------
    def fence_active(self) -> bool:
        g = self.controller.geofence
        return g is not None and g.enabled

    def height_cm(self) -> float:
        c = self.controller
        if c.last_height_cm is not None:
            return c.last_height_cm
        return c.position.z if c.flying else 0.0

    def recent_violation(self) -> bool:
        events = self.controller.violations.events
        recent = bool(events) and (datetime.now() - events[-1].timestamp).total_seconds() < 4
        return recent or self._gps_violating

    # -- mensagens -----------------------------------------------------------------
    def notify(self, text: str, kind: str = "info") -> None:
        """Mostra no banner do topo e grava no registro. kind: info | ok | error."""
        self.header.set_message(text, kind)
        self.log_panel.add(text, kind)

    def refresh(self) -> None:
        pos = self.controller.position
        if not self.trail or self.trail[-1] != pos:
            self.trail.append(pos)
            del self.trail[:-300]
        for panel in (self.header, self.sensor_panel, self.radar_panel, self.control_panel):
            panel.refresh()

    def reset_trail(self) -> None:
        self.trail = [self.controller.position]

    # -- teclado -------------------------------------------------------------------
    @staticmethod
    def _is_typing(widget) -> bool:
        """True se o foco está num campo de texto editável (não dispara voo)."""
        if isinstance(widget, tk.Text):
            return True
        if isinstance(widget, tk.Entry):
            return str(widget.cget("state")) == "normal"
        return False

    def _focused(self):
        try:
            return self.focus_get()
        except (KeyError, tk.TclError):   # bug conhecido do Tk com listas suspensas
            return None

    def _on_key_press(self, event) -> None:
        if self._is_typing(self._focused()):
            if event.keysym == "Escape":
                self.focus_set()          # Esc sai do campo de texto
            return
        action = resolve(event.keysym)
        if action is None:
            return
        self.control_panel.press(action, True)
        self.perform(action)

    def _on_key_release(self, event) -> None:
        action = resolve(event.keysym)
        if action is not None:
            self.control_panel.press(action, False)

    def _on_click(self, event) -> None:
        # Clicar fora de um campo de texto devolve o foco ao teclado de voo.
        if not isinstance(event.widget, (tk.Entry, tk.Text)):
            self.focus_set()

    # -- ações de voo (teclado e mouse passam por aqui) ----------------------------------
    def perform(self, action: Action, from_mouse: bool = False) -> None:
        c = self.controller
        if action in (Action.STEP_UP, Action.STEP_DOWN):
            self.config_panel.adjust_step(10 if action == Action.STEP_UP else -10)
            return
        if not c.is_connected():
            self.notify("Conecte ao drone primeiro (botão CONECTAR).", "error")
            return

        if action in MOVES:
            if not c.flying:
                self.notify("Decole primeiro (tecla T).", "error")
            elif not self.busy:           # tecla segurada: ignora enquanto há comando, sem fila
                self.move(action.value)
        elif action == Action.TAKEOFF:
            if c.flying:
                self.notify("O drone já está voando.")
            elif not self.busy:
                self.takeoff()
        elif action == Action.LAND:
            self.run_command(c.land, on_ok=lambda _: self.notify("Drone pousou.", "ok"))
        elif action == Action.EMERGENCY:
            # Mouse: clique deliberado. Teclado: exige Esc duas vezes.
            if from_mouse or self._emergency_gate.confirm(time.monotonic()):
                self.run_command(c.emergency, urgent=True,
                                 on_ok=lambda _: self.notify("EMERGÊNCIA: motores desligados.", "error"))
            else:
                self.notify("Pressione Esc de novo para confirmar a EMERGÊNCIA (desliga os motores).",
                            "error")

    def connect(self) -> None:
        self.notify("Conectando ao drone...")
        def ok(_):
            self.reset_trail()
            self.notify("Drone conectado. Decole com a tecla T.", "ok")
        self.run_command(self.controller.connect, on_ok=ok)

    def takeoff(self) -> None:
        def ok(_):
            self.reset_trail()
            self._auto_origin()
            self.notify("Decolou! Use W A S D e ↑ ↓.", "ok")
        self.run_command(self.controller.takeoff, on_ok=ok)

    def move(self, direction: str) -> None:
        self.run_command(lambda: self.controller.move(direction, self.config_panel.step_cm))

    # -- GPS ------------------------------------------------------------------------------
    def set_gps_origin(self, silent: bool = False) -> bool:
        fix = self.gps.latest
        if fix is None or fix.is_stale() or not fix.is_reliable:
            if not silent:
                self.notify("Sem GPS confiável para definir a origem.", "error")
            return False
        self.gps_origin = fix
        self._gps_violating = False
        self.notify(f"Origem GPS definida ({fix.lat:.6f}, {fix.lon:.6f}).", "ok")
        return True

    def _auto_origin(self) -> None:
        if self.gps_origin is None:
            self.set_gps_origin(silent=True)

    def _poll_gps(self) -> None:
        fix, origin = self.gps.latest, self.gps_origin
        if self.gps.error:
            self.gps_summary = ("erro", self.gps.error, T.DANGER)
        elif fix is None or fix.is_stale():
            self.gps_summary = ("sem sinal", "ESP não está enviando", T.WARN)
        elif not fix.is_reliable:
            self.gps_summary = (f"{fix.satellites} sat", f"sem fix confiável (HDOP {fix.hdop:.1f})", T.WARN)
        elif origin is None:
            self.gps_summary = (f"{fix.satellites} sat", "origem não definida", T.PRIMARY)
        else:
            east, north = local_offset_m(origin, fix)
            dist = math.hypot(east, north)
            self.gps_summary = (f"{dist:.1f} m", f"{fix.satellites} sat · da origem", T.OK)
            self._check_gps_geofence(east, north, dist)
        self.refresh()
        self.after(config.GPS_CHECK_INTERVAL_MS, self._poll_gps)

    def _check_gps_geofence(self, east_m: float, north_m: float, dist_m: float) -> None:
        c = self.controller
        if not self.fence_active():
            self._gps_violating = False
            return
        height = self.height_cm()
        reason = c.geofence.check(dist_m * 100, height)
        if reason is None:
            self._gps_violating = False
        elif not self._gps_violating:       # só age na 1ª leitura fora (sem repetir)
            self._gps_violating = True
            c.violations.record(Position(east_m * 100, north_m * 100, height), f"GPS: {reason}")
            self.notify(f"Violação pelo GPS: {reason}", "error")
            if self.config_panel.auto_land_enabled and c.is_connected() and c.flying:
                self.notify("Pousando automaticamente...", "error")
                self.run_command(c.land, urgent=True)

    # -- execução assíncrona --------------------------------------------------------------
    def run_command(self, fn: Callable, on_ok: Optional[Callable] = None,
                    on_err: Optional[Callable] = None, urgent: bool = False) -> None:
        """Executa `fn` fora da thread da UI; callbacks voltam na thread da UI."""
        self.busy += 1
        self.refresh()

        def job():
            try:
                self._results.put((on_ok, on_err, fn(), None))
            except Exception as exc:  # devolvemos qualquer erro para a UI tratar
                self._results.put((on_ok, on_err, None, exc))

        if urgent:
            threading.Thread(target=job, daemon=True).start()
        else:
            self._executor.submit(job)

    def _poll_results(self) -> None:
        try:
            while True:
                on_ok, on_err, value, exc = self._results.get_nowait()
                self.busy -= 1
                if exc is None:
                    if on_ok:
                        on_ok(value)
                else:
                    self._handle_error(exc, on_err)
                self.refresh()
        except queue.Empty:
            pass
        self.after(config.UI_POLL_INTERVAL_MS, self._poll_results)

    def _handle_error(self, exc: Exception, on_err: Optional[Callable]) -> None:
        if on_err:
            on_err(exc)
        elif isinstance(exc, GeofenceViolationError):
            self.notify(f"Movimento bloqueado pela cerca: {exc}", "error")
        elif isinstance(exc, DroneError):
            self.notify(str(exc), "error")
        else:
            self.notify(f"Erro inesperado: {exc}", "error")

    def _poll_telemetry(self) -> None:
        # Só consulta se estiver conectado e ocioso (não concorre com comandos).
        if self.controller.is_connected() and self.busy == 0:
            def ok(data):
                self.battery = data["battery"]
            self.run_command(self.controller.telemetry, on_ok=ok, on_err=lambda e: None)
        self.after(config.TELEMETRY_INTERVAL_MS, self._poll_telemetry)

    def on_close(self) -> None:
        self.gps.stop()
        self.controller.end()
        self._executor.shutdown(wait=False, cancel_futures=True)
        self.destroy()
