from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import flet as ft

from app import MeUbicasApp


def main(page: ft.Page) -> None:
    MeUbicasApp(page)


if __name__ == "__main__":
    ft.run(main)
