"""Ponto de entrada.

    python main.py          # com o drone Tello real
    python main.py --demo   # drone e GPS simulados (sem hardware)
"""
import argparse
import logging

from drone_commands import TelloController
from interface import App


def main() -> None:
    parser = argparse.ArgumentParser(description="Geofencing Lab")
    parser.add_argument("--demo", action="store_true",
                        help="usa drone e GPS simulados (não precisa de hardware)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if args.demo:
        from simulator import SimGps, SimTello
        controller = TelloController(tello_factory=SimTello)
        App(controller, gps=SimGps(controller)).mainloop()
    else:
        App().mainloop()


if __name__ == "__main__":
    main()
