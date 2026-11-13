"""Identidade visual (estilo educacional, inspirado no LEGO Education).

Fundo claro, cartões brancos com cantos arredondados, cores vivas e
fonte grande para leitura à distância.
"""
import customtkinter as ctk

# --- Paleta -------------------------------------------------------------------
BG = "#EEF2F9"
CARD = "#FFFFFF"
TILE = "#F4F7FC"
BORDER = "#DCE3F0"
INK = "#1B2A4A"
MUTED = "#6B7A99"
MUTED_LIGHT = "#A9B4CC"
DISABLED = "#F0F3F9"

PRIMARY = "#1E7FE0"
PRIMARY_HOVER = "#1768BC"
ACCENT = "#FFC20E"      # amarelo "tijolo" (tecla pressionada, destaques)
TEAL = "#13B5B1"
PURPLE = "#7B4FE0"
OK = "#27A55C"
WARN = "#F2A100"
DANGER = "#E5384B"

INFO_BG = "#E6F1FD"
OK_BG = "#E3F5EA"
ERROR_BG = "#FDE7EA"
GRID = "#E3E9F4"

RADIUS = 16


def font(size: int = 12, weight: str = "normal") -> ctk.CTkFont:
    # CTkFont só pode ser criada depois que a janela principal existe.
    return ctk.CTkFont(family="Segoe UI", size=size, weight=weight)


def level_color(ratio: float, higher_is_better: bool = False) -> str:
    """Verde/amarelo/vermelho conforme a proporção (0 a 1).

    higher_is_better=True  -> bateria (baixo é ruim)
    higher_is_better=False -> distância/altura vs. limite (alto é ruim)
    """
    if higher_is_better:
        return OK if ratio > 0.5 else WARN if ratio > 0.2 else DANGER
    return OK if ratio < 0.75 else WARN if ratio < 1.0 else DANGER
