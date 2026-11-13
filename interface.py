"""Interface gráfica (CustomTkinter).

Estrutura:
    App                -> janela principal; orquestra tudo
    ConfigFrame        -> modo de operação, distância por movimento, geofence
    StatusFrame        -> conexão, posição, bateria, botão CONECTAR
    MonitorFrame       -> histórico de violações do perímetro
    ControlFrame       -> botões de voo

Regra de ouro do Tkinter: só a thread principal mexe nos widgets. Comandos ao
drone são lentos (bloqueiam até o Tello responder), então rodam numa thread
de trabalho e devolvem o resultado por uma fila, lida pela thread principal
via `after()`.
"""
from __future__ import annotations

import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional

import customtkinter as ctk

import config
from drone_commands import (DroneError, GeofenceViolationError, TelloController)
from geofence import Geofence

FONT = ("Arial", 12)
FONT_TITLE = ("Arial", 20)


class ConfigFrame(ctk.CTkFrame):
    def __init__(self, master, app: "App"):
        super().__init__(master)
        self.app = app
        self.columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Configurações", font=FONT_TITLE).grid(
            row=0, column=0, pady=(8, 4))

        ctk.CTkLabel(self, text="Modo de operação:", font=FONT).grid(
            row=1, column=0, sticky="w", padx=20)
        self.mode = ctk.CTkComboBox(
            self, values=[config.MODE_FREE, config.MODE_FENCED],
            command=lambda _: self.apply())
        self.mode.grid(row=2, column=0, padx=20, pady=(0, 8), sticky="ew")

        self.step_label = ctk.CTkLabel(self, font=FONT)
        self.step_label.grid(row=3, column=0, sticky="w", padx=20)
        self.step = ctk.CTkSlider(
            self, from_=config.MIN_MOVE_CM, to=config.MAX_MOVE_CM,
            number_of_steps=(config.MAX_MOVE_CM - config.MIN_MOVE_CM) // 10,
            command=self._on_step)
        self.step.set(config.DEFAULT_MOVE_CM)
        self.step.grid(row=4, column=0, padx=20, pady=(0, 8), sticky="ew")
        self._on_step(config.DEFAULT_MOVE_CM)

        ctk.CTkLabel(self, text="Raio de delimitação (m):", font=FONT).grid(
            row=5, column=0, sticky="w", padx=20)
        self.radius = ctk.CTkEntry(self)
        self.radius.insert(0, str(config.DEFAULT_RADIUS_M))
        self.radius.grid(row=6, column=0, padx=20, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(self, text="Altura máxima (m):", font=FONT).grid(
            row=7, column=0, sticky="w", padx=20)
        self.height = ctk.CTkEntry(self)
        self.height.insert(0, str(config.DEFAULT_MAX_HEIGHT_M))
        self.height.grid(row=8, column=0, padx=20, pady=(0, 8), sticky="ew")

        ctk.CTkButton(self, text="APLICAR", font=FONT, command=self.apply).grid(
            row=9, column=0, pady=(4, 12))

    @property
    def step_cm(self) -> int:
        # arredonda para múltiplos de 10 (o slider devolve float)
        return int(round(self.step.get() / 10) * 10)

    def _on_step(self, value) -> None:
        self.step_label.configure(text=f"Distância por movimento: {int(round(float(value) / 10) * 10)} cm")

    def apply(self) -> None:
        """Lê os campos, valida e instala (ou remove) o geofence no controlador."""
        if self.mode.get() == config.MODE_FREE:
            self.app.controller.geofence = None
            self.app.notify("Voo livre: delimitação desativada.")
        else:
            try:
                radius_m = float(self.radius.get().replace(",", "."))
                height_m = float(self.height.get().replace(",", "."))
                if radius_m <= 0 or height_m <= 0:
                    raise ValueError
            except ValueError:
                self.app.notify("Raio e altura devem ser números maiores que zero.", error=True)
                return
            self.app.controller.geofence = Geofence(radius_m * 100, height_m * 100)
            self.app.notify(f"Delimitação ativa: raio {radius_m:g} m, altura {height_m:g} m.")
        self.app.refresh()


class StatusFrame(ctk.CTkFrame):
    def __init__(self, master, app: "App"):
        super().__init__(master)
        self.app = app
        self.columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Status do Drone", font=FONT_TITLE).grid(
            row=0, column=0, pady=(8, 4))
        self.conn = ctk.CTkLabel(self, font=FONT)
        self.mode = ctk.CTkLabel(self, font=FONT)
        self.pos = ctk.CTkLabel(self, font=FONT)
        self.dist = ctk.CTkLabel(self, font=FONT)
        self.battery = ctk.CTkLabel(self, font=FONT)
        self.msg = ctk.CTkLabel(self, font=FONT, wraplength=280, justify="left")
        for i, w in enumerate((self.conn, self.mode, self.pos, self.dist, self.battery), start=1):
            w.grid(row=i, column=0, sticky="w", padx=20, pady=2)
        self.msg.grid(row=6, column=0, sticky="w", padx=20, pady=(6, 2))

        self.button = ctk.CTkButton(self, text="CONECTAR", font=FONT, command=app.connect)
        self.button.grid(row=7, column=0, pady=(8, 12))
        self.battery_value: Optional[int] = None

    def refresh(self) -> None:
        c = self.app.controller
        if c.is_connected():
            self.conn.configure(text="Conectado", text_color="green")
        else:
            self.conn.configure(text="Desconectado", text_color="red")
        fenced = c.geofence is not None and c.geofence.enabled
        self.mode.configure(
            text=f"Modo: {'Delimitação' if fenced else 'Voo livre'}",
            text_color="green" if fenced else "gray")
        p = c.position
        self.pos.configure(text=f"Pos (x, y, z): {p.x:.0f}, {p.y:.0f}, {p.z:.0f} cm")
        if fenced:
            self.dist.configure(
                text=f"Distância da origem: {p.horizontal_distance_cm / 100:.2f} m "
                     f"/ {c.geofence.radius_cm / 100:.2f} m")
        else:
            self.dist.configure(text="Distância da origem: N/A")
        self.battery.configure(
            text="Bateria: --" if self.battery_value is None else f"Bateria: {self.battery_value}%")
        self.button.configure(state="disabled" if self.app.busy or c.is_connected() else "normal")

    def set_message(self, text: str, error: bool = False) -> None:
        self.msg.configure(text=text, text_color="red" if error else ("gray20", "gray80"))


class MonitorFrame(ctk.CTkFrame):
    """Mostra o histórico de violações do perímetro."""

    def __init__(self, master, app: "App"):
        super().__init__(master)
        self.app = app
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Monitoramento de violações", font=FONT_TITLE).grid(
            row=0, column=0, pady=(8, 4))
        self.box = ctk.CTkTextbox(self, state="disabled")
        self.box.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self._shown = 0

    def refresh(self) -> None:
        events = self.app.controller.violations.events
        if len(events) == self._shown:
            return
        self.box.configure(state="normal")
        for event in events[self._shown:]:
            self.box.insert("end", str(event) + "\n")
        self.box.see("end")
        self.box.configure(state="disabled")
        self._shown = len(events)


class ControlFrame(ctk.CTkFrame):
    def __init__(self, master, app: "App"):
        super().__init__(master)
        self.app = app
        ctk.CTkLabel(self, text="Controles do Drone", font=FONT_TITLE).grid(
            row=0, column=0, columnspan=5, sticky="w", padx=20, pady=(8, 4))

        self.movers: list[ctk.CTkButton] = []     # só funcionam quando livres
        self.safety: list[ctk.CTkButton] = []     # sempre disponíveis se conectado

        def add(text, row, col, command, group, color=None):
            kw = {"fg_color": color, "hover_color": color} if color else {}
            b = ctk.CTkButton(self, text=text, font=FONT, state="disabled", command=command, **kw)
            b.grid(row=row, column=col, padx=8, pady=6)
            group.append(b)

        add("DECOLAR", 1, 0, lambda: app.run_command(app.controller.takeoff), self.movers)
        add("POUSAR", 2, 0, lambda: app.run_command(app.controller.land), self.safety)
        add("EMERGÊNCIA", 3, 0, app.emergency, self.safety, color="#b00020")
        add("FRENTE", 1, 2, lambda: app.move("forward"), self.movers)
        add("ESQUERDA", 2, 1, lambda: app.move("left"), self.movers)
        add("TRÁS", 2, 2, lambda: app.move("back"), self.movers)
        add("DIREITA", 2, 3, lambda: app.move("right"), self.movers)
        add("SUBIR", 3, 1, lambda: app.move("up"), self.movers)
        add("DESCER", 3, 3, lambda: app.move("down"), self.movers)

    def refresh(self) -> None:
        connected = self.app.controller.is_connected()
        free = connected and not self.app.busy
        for b in self.movers:
            b.configure(state="normal" if free else "disabled")
        for b in self.safety:
            b.configure(state="normal" if connected else "disabled")


class App(ctk.CTk):
    def __init__(self, controller: Optional[TelloController] = None):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.title(config.WINDOW_TITLE)
        self.geometry(config.WINDOW_SIZE)
        self.minsize(900, 600)

        self.controller = controller or TelloController()
        self.busy = 0                                   # nº de comandos em andamento
        self._executor = ThreadPoolExecutor(max_workers=1)  # serializa comandos
        self._results: queue.Queue = queue.Queue()      # threads -> UI

        self.columnconfigure(0, weight=1, uniform="c")
        self.columnconfigure(1, weight=2, uniform="c")
        self.rowconfigure(0, weight=3)
        self.rowconfigure(1, weight=2)

        self.config_frame = ConfigFrame(self, self)
        self.status_frame = StatusFrame(self, self)
        self.monitor_frame = MonitorFrame(self, self)
        self.control_frame = ControlFrame(self, self)
        self.config_frame.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=(16, 8))
        self.status_frame.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=(8, 16))
        self.monitor_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=(16, 8))
        self.control_frame.grid(row=1, column=1, sticky="nsew", padx=(8, 16), pady=(8, 16))

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.refresh()
        self.after(config.UI_POLL_INTERVAL_MS, self._poll_results)
        self.after(config.TELEMETRY_INTERVAL_MS, self._poll_telemetry)

    # -- API usada pelos frames -------------------------------------------------
    def notify(self, text: str, error: bool = False) -> None:
        self.status_frame.set_message(text, error)

    def refresh(self) -> None:
        for frame in (self.status_frame, self.monitor_frame, self.control_frame):
            frame.refresh()

    def connect(self) -> None:
        self.notify("Conectando...")
        self.run_command(self.controller.connect, on_ok=lambda _: self.notify("Drone conectado."))

    def move(self, direction: str) -> None:
        self.run_command(lambda: self.controller.move(direction, self.config_frame.step_cm))

    def emergency(self) -> None:
        # Fora da fila: precisa agir mesmo que outro comando esteja travado.
        self.run_command(self.controller.emergency, urgent=True)

    # -- execução assíncrona ------------------------------------------------------
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
            self.notify(f"Movimento bloqueado: {exc}", error=True)
        elif isinstance(exc, DroneError):
            self.notify(str(exc), error=True)
        else:
            self.notify(f"Erro inesperado: {exc}", error=True)

    def _poll_telemetry(self) -> None:
        # Só consulta se estiver conectado e ocioso (não concorre com comandos).
        if self.controller.is_connected() and self.busy == 0:
            def ok(data):
                self.status_frame.battery_value = data["battery"]
            self.run_command(self.controller.telemetry, on_ok=ok, on_err=lambda e: None)
        self.after(config.TELEMETRY_INTERVAL_MS, self._poll_telemetry)

    def on_close(self) -> None:
        self.controller.end()
        self._executor.shutdown(wait=False, cancel_futures=True)
        self.destroy()
