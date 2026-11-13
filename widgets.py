"""Componentes visuais reutilizáveis: cartão, sensor, tecla, radar e medidor de altura."""
from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk

import theme as T
from geofence import Geofence, Position


class Card(ctk.CTkFrame):
    """Cartão branco arredondado com título. Coloque o conteúdo em `card.body`."""

    def __init__(self, master, title: Optional[str] = None, accent: str = T.PRIMARY,
                 subtitle: Optional[str] = None):
        super().__init__(master, fg_color=T.CARD, corner_radius=T.RADIUS,
                         border_width=1, border_color=T.BORDER)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        if title:
            ctk.CTkFrame(head, width=10, height=10, corner_radius=5,
                         fg_color=accent).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(head, text=title, font=T.font(15, "bold"),
                         text_color=T.INK).pack(side="left")
        if subtitle:
            ctk.CTkLabel(head, text=subtitle, font=T.font(11),
                         text_color=T.MUTED).pack(side="right")
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))


class SensorTile(ctk.CTkFrame):
    """Leitura de um sensor, no estilo dos monitores do EV3 Classroom."""

    def __init__(self, master, title: str, with_bar: bool = True):
        super().__init__(master, fg_color=T.TILE, corner_radius=14)
        self.columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title.upper(), font=T.font(10, "bold"),
                     text_color=T.MUTED, anchor="w").grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))
        self.value = ctk.CTkLabel(self, text="--", font=T.font(22, "bold"),
                                  text_color=T.INK, anchor="w")
        self.value.grid(row=1, column=0, sticky="w", padx=12)
        self.sub = ctk.CTkLabel(self, text="", font=T.font(10), text_color=T.MUTED,
                                anchor="w", justify="left", wraplength=135)
        self.sub.grid(row=2, column=0, sticky="w", padx=12)
        self.bar: Optional[ctk.CTkProgressBar] = None
        if with_bar:
            self.bar = ctk.CTkProgressBar(self, height=6, corner_radius=3,
                                          fg_color=T.BORDER, progress_color=T.PRIMARY)
            self.bar.set(0)
            self.bar.grid(row=3, column=0, sticky="ew", padx=12, pady=(2, 10))
        else:
            ctk.CTkFrame(self, height=8, fg_color="transparent").grid(row=3, column=0)
        self._key = None

    def set(self, value: str, sub: str = "", ratio: Optional[float] = None,
            color: str = T.PRIMARY) -> None:
        key = (value, sub, None if ratio is None else round(ratio, 3), color)
        if key == self._key:           # evita redesenhar à toa
            return
        self._key = key
        self.value.configure(text=value, text_color=T.INK if color == T.PRIMARY else color)
        self.sub.configure(text=sub)
        if self.bar is not None:
            self.bar.configure(progress_color=color)
            self.bar.set(0 if ratio is None else max(0.0, min(1.0, ratio)))


class KeyCap(ctk.CTkFrame):
    """Tecla clicável com legenda. Acende quando a tecla física é pressionada."""

    def __init__(self, master, key_text: str, caption: str, command: Callable,
                 width: int = 54, danger: bool = False):
        super().__init__(master, fg_color="transparent")
        self._danger = danger
        self._enabled = False
        self._pressed = False
        self.btn = ctk.CTkButton(self, text=key_text, width=width, height=46, corner_radius=10,
                                 font=T.font(16, "bold"), border_width=2,
                                 command=command, hover=False)
        self.btn.pack()
        ctk.CTkLabel(self, text=caption, font=T.font(10), text_color=T.MUTED).pack(pady=(2, 0))
        self._apply()

    def set_enabled(self, enabled: bool) -> None:
        if enabled != self._enabled:
            self._enabled = enabled
            self._apply()

    def press(self, pressed: bool) -> None:
        if pressed != self._pressed:
            self._pressed = pressed
            self._apply()

    def _apply(self) -> None:
        if self._pressed:
            fg, tc, bc = (T.ACCENT, T.INK, T.WARN) if self._enabled else (T.ERROR_BG, T.DANGER, T.DANGER)
        elif not self._enabled:
            fg, tc, bc = T.DISABLED, T.MUTED_LIGHT, T.BORDER
        elif self._danger:
            fg, tc, bc = T.DANGER, "white", T.DANGER
        else:
            fg, tc, bc = T.CARD, T.INK, T.MUTED_LIGHT
        # O botão fica sempre "normal": o estado habilitado é decidido pelo app,
        # assim o clique em tecla desabilitada ainda explica o motivo ao usuário.
        self.btn.configure(fg_color=fg, text_color=tc, border_color=bc)


def _nice_step(target: float) -> float:
    for s in (0.5, 1, 2, 5, 10, 20, 25, 50, 100, 200, 500):
        if s >= target:
            return s
    return 1000


class RadarCanvas(ctk.CTkFrame):
    """Vista de cima: círculo do geofence, trilha e drone."""

    def __init__(self, master):
        super().__init__(master, fg_color=T.TILE, corner_radius=14)
        self.canvas = tk.Canvas(self, bg=T.TILE, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)
        self.canvas.bind("<Configure>", lambda _e: self._paint())
        self._last = (Position(), [], None, "idle")

    def render(self, pos: Position, trail: list, fence: Optional[Geofence], state: str) -> None:
        self._last = (pos, trail, fence, state)
        self._paint()

    def _paint(self) -> None:
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 80 or h < 80:
            return
        pos, trail, fence, state = self._last
        cx, cy = w / 2, h / 2
        half = min(w, h) / 2 - 22
        fenced = fence is not None and fence.enabled
        if fenced:
            view_m = fence.radius_cm / 100 * 1.15
        else:
            far = max([5.0, abs(pos.x) / 100, abs(pos.y) / 100]
                      + [max(abs(p.x), abs(p.y)) / 100 for p in trail])
            view_m = far * 1.2
        scale = half / view_m
        bad = state == "violation"

        if fenced:                                   # área permitida
            r = fence.radius_cm / 100 * scale
            c.create_oval(cx - r, cy - r, cx + r, cy + r,
                          fill=T.ERROR_BG if bad else T.INFO_BG,
                          outline=T.DANGER if bad else T.PRIMARY, width=3)
        step = _nice_step(view_m / 3)                # anéis de distância
        r_m = step
        while r_m <= view_m * 1.001:
            r = r_m * scale
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=T.MUTED_LIGHT, dash=(3, 4))
            c.create_text(cx + 5, cy - r - 8, text=f"{r_m:g} m", fill=T.MUTED,
                          font=("Segoe UI", 8), anchor="w")
            r_m += step
        c.create_line(cx - half, cy, cx + half, cy, fill=T.GRID)
        c.create_line(cx, cy - half, cx, cy + half, fill=T.GRID)
        for text, x, y in (("FRENTE", cx, 10), ("TRÁS", cx, h - 10),
                           ("ESQ", 16, cy), ("DIR", w - 16, cy)):
            c.create_text(x, y, text=text, fill=T.MUTED, font=("Segoe UI", 8, "bold"))

        # origem (ponto de decolagem)
        c.create_rectangle(cx - 5, cy - 5, cx + 5, cy + 5, fill=T.CARD, outline=T.INK, width=2)
        c.create_text(cx + 9, cy + 12, text="origem", fill=T.INK, font=("Segoe UI", 8), anchor="w")

        pts = []
        for p in trail:
            pts += [cx + p.x / 100 * scale, cy - p.y / 100 * scale]
        if len(pts) >= 4:
            c.create_line(*pts, fill=T.PRIMARY, width=2, smooth=True)

        px, py = cx + pos.x / 100 * scale, cy - pos.y / 100 * scale
        color = T.DANGER if bad else (T.PRIMARY if state == "flying" else T.MUTED)
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):    # hélices
            c.create_line(px, py, px + dx * 12, py + dy * 12, fill=color, width=2)
            c.create_oval(px + dx * 12 - 5, py + dy * 12 - 5, px + dx * 12 + 5, py + dy * 12 + 5,
                          outline=color, width=2, fill=T.CARD)
        c.create_oval(px - 7, py - 7, px + 7, py + 7, fill=color, outline=T.CARD, width=2)
        c.create_polygon(px, py - 14, px - 4, py - 8, px + 4, py - 8, fill=T.ACCENT, outline="")


class HeightGauge(ctk.CTkFrame):
    """Medidor vertical de altura, com marca da altura máxima permitida."""

    def __init__(self, master):
        super().__init__(master, fg_color=T.TILE, corner_radius=14, width=84)
        self.canvas = tk.Canvas(self, bg=T.TILE, highlightthickness=0, bd=0, width=80)
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)
        self.canvas.bind("<Configure>", lambda _e: self._paint())
        self._last = (0.0, None)

    def render(self, height_cm: float, fence: Optional[Geofence]) -> None:
        self._last = (height_cm, fence)
        self._paint()

    def _paint(self) -> None:
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if h < 80:
            return
        height_cm, fence = self._last
        fenced = fence is not None and fence.enabled
        top = fence.max_height_cm * 1.2 if fenced else 300.0
        x0, x1, y_top, y_bot = w / 2 - 12, w / 2 + 12, 30, h - 34
        c.create_text(w / 2, 12, text="ALTURA", fill=T.MUTED, font=("Segoe UI", 8, "bold"))
        c.create_rectangle(x0, y_top, x1, y_bot, fill=T.BORDER, outline="")
        ratio = max(0.0, min(1.0, height_cm / top))
        y_val = y_bot - (y_bot - y_top) * ratio
        over = fenced and height_cm > fence.max_height_cm
        c.create_rectangle(x0, y_val, x1, y_bot, fill=T.DANGER if over else T.TEAL, outline="")
        if fenced:
            y_max = y_bot - (y_bot - y_top) * (fence.max_height_cm / top)
            c.create_line(x0 - 8, y_max, x1 + 8, y_max, fill=T.DANGER, width=2, dash=(4, 3))
            c.create_text(w / 2, y_max - 8, text=f"máx {fence.max_height_cm / 100:g} m",
                          fill=T.DANGER, font=("Segoe UI", 8))
        c.create_text(w / 2, h - 16, text=f"{height_cm / 100:.2f} m", fill=T.INK,
                      font=("Segoe UI", 11, "bold"))
