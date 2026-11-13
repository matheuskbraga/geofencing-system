"""Ponto de entrada: python main.py"""
import logging

from interface import App

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    App().mainloop()
