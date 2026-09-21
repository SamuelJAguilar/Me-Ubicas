from __future__ import annotations

from pathlib import Path

import flet as ft

from models import Character
from theme import CARD, CREAM, GOLD, MUTED, NAVY_DEEP


def portrait(path: str, *, expand: bool = True, height: int | None = None) -> ft.Control:
    file_path = Path(path) if path else None
    if file_path and file_path.is_file():
        image = ft.Image(
            src=str(file_path),
            fit=ft.BoxFit.COVER,
            expand=expand,
            width=None if expand else 120,
            height=height,
        )
    else:
        image = ft.Container(
            expand=expand,
            height=height,
            bgcolor=CARD,
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(ft.Icons.PERSON, size=42, color=GOLD),
        )
    return ft.Container(
        expand=expand,
        height=height,
        bgcolor=NAVY_DEEP,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=image,
    )


def character_card(
    character: Character,
    *,
    discarded: bool = False,
    selected: bool = False,
    on_click=None,
) -> ft.Control:
    overlay = ft.Container(
        expand=True,
        bgcolor="#B3000000",
        alignment=ft.Alignment.CENTER,
        visible=discarded,
        content=ft.Icon(ft.Icons.CLOSE, color=CREAM, size=36),
    )
    return ft.Container(
        bgcolor=CARD,
        border_radius=14,
        padding=6,
        border=ft.Border.all(3, GOLD if selected else "#00000000"),
        on_click=on_click,
        content=ft.Column(
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Stack(
                    expand=True,
                    controls=[portrait(character.image_path), overlay],
                ),
                ft.Text(
                    character.name,
                    size=12,
                    color=CREAM,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    weight=ft.FontWeight.W_600,
                ),
            ],
        ),
    )


def section_title(text: str) -> ft.Text:
    return ft.Text(text, size=14, weight=ft.FontWeight.W_700, color=GOLD)


def hint(text: str) -> ft.Text:
    return ft.Text(text, size=12, color=MUTED)
