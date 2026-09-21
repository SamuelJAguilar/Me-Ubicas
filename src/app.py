from __future__ import annotations

from pathlib import Path

import flet as ft

from game_logic import (
    AlreadyAskedError,
    AlreadyAskedThisTurnError,
    GameError,
    GameSession,
    pick_boards,
)
from models import Character, Classification, ClassificationValue
from storage import Store, copy_image as save_image
from theme import (
    CARD,
    CARD_SOFT,
    CORAL,
    CREAM,
    DANGER,
    GOLD,
    GOLD_DARK,
    MUTED,
    NAVY,
    NAVY_DEEP,
    SUCCESS,
    TEAL,
    WHITE,
)
from widgets import character_card, hint, portrait


CLASS_ICONS = {
    "ojos": ft.Icons.REMOVE_RED_EYE,
    "pelo": ft.Icons.BRUSH,
    "piel": ft.Icons.PALETTE,
    "sexo": ft.Icons.WC,
    "edad": ft.Icons.CAKE,
    "bello_facial": ft.Icons.FACE,
    "accesorios": ft.Icons.DIAMOND,
}


class MeUbicasApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.store = Store()
        self.file_picker = ft.FilePicker()
        self.game: GameSession | None = None
        self.form_id: int | None = None
        self.form_name = ""
        self.form_image = ""
        self.form_traits: dict[int, set[int]] = {}
        self.pick_player = 1
        self.picked_id: int | None = None
        self.after_pass = None
        self.pass_to = 1
        self._configure_page()
        self.show_home()

    def _configure_page(self) -> None:
        self.page.title = "¿Me ubicas?"
        self.page.padding = 0
        self.page.bgcolor = NAVY
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.theme = ft.Theme(color_scheme_seed=GOLD)
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.services.append(self.file_picker)
        try:
            self.page.window.width = 420
            self.page.window.height = 860
        except Exception:
            pass

    def toast(self, message: str) -> None:
        self.page.show_dialog(ft.SnackBar(ft.Text(message)))

    def close_dialog(self, _e=None) -> None:
        self.page.pop_dialog()

    def _alert(
        self,
        *,
        title: str,
        message: str,
        tone: str = "warning",
        confirm_label: str | None = "Continuar",
        on_confirm=None,
        cancel_label: str | None = "Cancelar",
        extra: ft.Control | None = None,
    ) -> None:
        styles = {
            "warning": (ft.Icons.WARNING_AMBER_ROUNDED, GOLD_DARK, "#FFF6E5", "Revisa bien antes de continuar."),
            "danger": (ft.Icons.REPORT, DANGER, "#FDECEC", "Esta acción no se puede deshacer."),
            "success": (ft.Icons.CHECK_CIRCLE, SUCCESS, "#E8F7EE", None),
            "info": (ft.Icons.HELP, TEAL, "#E8F5F6", None),
        }
        icon, accent, tint, caution = styles.get(tone, styles["warning"])
        blocks: list[ft.Control] = [
            ft.Container(
                width=72,
                height=72,
                border_radius=36,
                bgcolor=tint,
                border=ft.Border.all(width=2, color=accent),
                alignment=ft.Alignment.CENTER,
                content=ft.Icon(icon, color=accent, size=38),
            ),
            ft.Text(
                title,
                size=20,
                weight=ft.FontWeight.BOLD,
                color=NAVY,
                text_align=ft.TextAlign.CENTER,
            ),
        ]
        if caution:
            blocks.append(
                ft.Container(
                    bgcolor=tint,
                    border=ft.Border.all(width=1, color=accent),
                    border_radius=12,
                    padding=10,
                    content=ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.PRIORITY_HIGH, color=accent, size=20),
                            ft.Text(caution, color=NAVY, size=13, weight=ft.FontWeight.W_600, expand=True),
                        ],
                    ),
                )
            )
        if message:
            blocks.append(
                ft.Text(
                    message,
                    size=14,
                    color="#3D4A57",
                    text_align=ft.TextAlign.CENTER,
                )
            )
        if extra:
            blocks.append(ft.Container(width=float("inf"), content=extra))
        actions = []
        if cancel_label:
            actions.append(
                ft.Button(
                    content=cancel_label,
                    bgcolor=WHITE,
                    color=NAVY,
                    style=ft.ButtonStyle(
                        side=ft.BorderSide(1, "#C5D0DC"),
                        shape=ft.RoundedRectangleBorder(radius=12),
                    ),
                    on_click=self.close_dialog,
                )
            )
        if confirm_label and on_confirm:
            actions.append(
                ft.Button(
                    content=confirm_label,
                    bgcolor=accent,
                    color=WHITE,
                    on_click=on_confirm,
                )
            )
        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                bgcolor=WHITE,
                elevation=16,
                shadow_color="#66000000",
                shape=ft.RoundedRectangleBorder(radius=22),
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=blocks,
                ),
                actions=actions,
                actions_alignment=ft.MainAxisAlignment.END if cancel_label else ft.MainAxisAlignment.CENTER,
            )
        )

    def paint(
        self,
        body: ft.Control,
        *,
        title: str | None = None,
        on_back=None,
        actions: list[ft.Control] | None = None,
        fab: ft.Control | None = None,
    ) -> None:
        if title:
            leading = None
            if on_back:
                leading = ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=CREAM,
                    on_click=lambda e: on_back(),
                )
            self.page.appbar = ft.AppBar(
                leading=leading,
                title=ft.Text(title, color=CREAM, weight=ft.FontWeight.W_700),
                bgcolor=NAVY_DEEP,
                center_title=True,
                actions=actions or [],
            )
        else:
            self.page.appbar = None
        self.page.floating_action_button = fab
        self.page.controls.clear()
        self.page.add(body)

    def screen(self, *controls: ft.Control, scroll: bool = True) -> ft.Control:
        return ft.SafeArea(
            expand=True,
            content=ft.Container(
                expand=True,
                bgcolor=NAVY,
                padding=16,
                content=ft.Column(
                    expand=True,
                    spacing=14,
                    scroll=ft.ScrollMode.AUTO if scroll else None,
                    controls=list(controls),
                ),
            ),
        )

    def show_home(self) -> None:
        self.game = None
        self.paint(
            self.screen(
                ft.Container(height=24),
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=ft.Container(
                        width=108,
                        height=108,
                        bgcolor=CARD,
                        border_radius=54,
                        alignment=ft.Alignment.CENTER,
                        border=ft.Border.all(width=3, color=GOLD),
                        content=ft.Icon(ft.Icons.PERSON_SEARCH, size=54, color=GOLD),
                    ),
                ),
                ft.Text(
                    "¿Me ubicas?",
                    size=36,
                    weight=ft.FontWeight.BOLD,
                    color=GOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Adivina el personaje del otro jugador.\nSe juega en el mismo celular, turnándose.",
                    color=MUTED,
                    text_align=ft.TextAlign.CENTER,
                    size=14,
                ),
                ft.Container(height=12),
                self._home_tile(
                    "Crear personajes",
                    "Fotos, clasificaciones y características nuevas",
                    ft.Icons.PERSON_ADD_ALT_1,
                    TEAL,
                    self.show_characters,
                ),
                self._home_tile(
                    "Jugar",
                    "Hasta 20 personajes al azar por jugador",
                    ft.Icons.SPORTS_ESPORTS,
                    CORAL,
                    self.start_game,
                ),
            ),
            title=None,
            fab=None,
        )

    def _home_tile(self, title: str, subtitle: str, icon, color: str, on_click) -> ft.Control:
        return ft.Container(
            bgcolor=CARD,
            border_radius=22,
            padding=18,
            on_click=lambda e: on_click(),
            content=ft.Row(
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=56,
                        height=56,
                        bgcolor=color,
                        border_radius=16,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(icon, color=NAVY_DEEP, size=28),
                    ),
                    ft.Column(
                        spacing=4,
                        expand=True,
                        controls=[
                            ft.Text(title, size=18, weight=ft.FontWeight.W_700, color=CREAM),
                            ft.Text(subtitle, size=13, color=MUTED),
                        ],
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=GOLD),
                ],
            ),
        )

    def show_characters(self) -> None:
        characters = self.store.characters()
        cards: list[ft.Control] = []
        if not characters:
            cards.append(
                ft.Container(
                    bgcolor=CARD,
                    border_radius=18,
                    padding=24,
                    content=ft.Column(
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.PERSON_OFF, color=GOLD, size=40),
                            ft.Text("Todavía no hay personajes", color=CREAM, size=16),
                            hint("Agrega una foto y elige sus características."),
                        ],
                    ),
                )
            )
        for character in characters:
            cards.append(self._character_list_tile(character))
        self.paint(
            self.screen(
                hint("Pulsa + para crear uno, o entra a una ficha para editarla."),
                *cards,
                ft.Container(height=72),
            ),
            title="Personajes",
            on_back=self.show_home,
            actions=[
                ft.IconButton(
                    icon=ft.Icons.CATEGORY,
                    icon_color=GOLD,
                    tooltip="Clasificaciones",
                    on_click=lambda e: self.show_classifications(),
                )
            ],
            fab=ft.FloatingActionButton(
                icon=ft.Icons.ADD,
                bgcolor=GOLD,
                foreground_color=WHITE,
                on_click=lambda e: self.show_character_form(),
            ),
        )

    def _character_list_tile(self, character: Character) -> ft.Control:
        return ft.Container(
            bgcolor=CARD,
            border_radius=18,
            padding=10,
            on_click=lambda e, cid=character.id: self.show_character_form(cid),
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=64,
                        height=64,
                        border_radius=14,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=portrait(character.image_path, expand=True),
                    ),
                    ft.Column(
                        expand=True,
                        spacing=4,
                        controls=[
                            ft.Text(character.name, color=CREAM, size=16, weight=ft.FontWeight.W_600),
                            hint(self._trait_summary(character)),
                        ],
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=DANGER,
                        on_click=lambda e, cid=character.id, name=character.name: self._confirm_delete(cid, name),
                    ),
                ],
            ),
        )

    def _trait_summary(self, character: Character) -> str:
        names = []
        values = {item.id: item for item in self.store.all_values()}
        for value_id in sorted(character.value_ids()):
            value = values.get(value_id)
            if value:
                names.append(value.name)
        return ", ".join(names[:6]) if names else "Sin características"

    def _confirm_delete(self, character_id: int, name: str) -> None:
        self._alert(
            title="Eliminar personaje",
            message=f"Vas a borrar a {name}. Si continúas, desaparecerá de la lista y de las partidas nuevas.",
            tone="danger",
            confirm_label="Eliminar",
            on_confirm=lambda e, cid=character_id: self._delete_character(cid),
            cancel_label="Cancelar",
        )

    def _delete_character(self, character_id: int) -> None:
        self.store.delete_character(character_id)
        self.close_dialog()
        self.show_characters()

    def show_classifications(self) -> None:
        blocks: list[ft.Control] = [
            hint("Cada clasificación tiene elementos. Puedes crear más, por ejemplo Pelo → Blanco.")
        ]
        for classification in self.store.classifications():
            values = self.store.values(classification.id)
            chips = [
                ft.Chip(label=value.name, bgcolor=CARD_SOFT)
                for value in values
            ]
            chips.append(
                ft.Chip(
                    label=ft.Text("+ Nuevo", color=WHITE, weight=ft.FontWeight.W_700),
                    leading=ft.Icon(ft.Icons.ADD, size=16, color=WHITE),
                    bgcolor=GOLD,
                    on_click=lambda e, item=classification: self._prompt_new_value(
                        item, on_saved=lambda _value: self.show_classifications()
                    ),
                )
            )
            blocks.append(
                ft.Container(
                    bgcolor=CARD,
                    border_radius=18,
                    padding=14,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(CLASS_ICONS.get(classification.slug, ft.Icons.LABEL), color=GOLD),
                                    ft.Text(
                                        classification.name,
                                        color=CREAM,
                                        weight=ft.FontWeight.W_700,
                                        size=16,
                                    ),
                                    ft.Text(
                                        "varios" if classification.multi_select else "uno",
                                        color=MUTED,
                                        size=12,
                                    ),
                                ]
                            ),
                            ft.Row(wrap=True, spacing=8, run_spacing=8, controls=chips),
                        ],
                    ),
                )
            )
        self.paint(
            self.screen(*blocks),
            title="Clasificaciones",
            on_back=self.show_characters,
        )

    def show_character_form(self, character_id: int | None = None) -> None:
        self.form_id = character_id
        if character_id:
            character = self.store.character(character_id)
            if character is None:
                self.toast("No se encontró el personaje.")
                self.show_characters()
                return
            self.form_name = character.name
            self.form_image = character.image_path
            self.form_traits = {key: set(value) for key, value in character.traits.items()}
        else:
            self.form_name = ""
            self.form_image = ""
            self.form_traits = {}
        self._render_character_form()

    def _render_character_form(self) -> None:
        name_field = ft.TextField(
            label="Nombre",
            value=self.form_name,
            on_change=lambda e: setattr(self, "form_name", e.control.value or ""),
            border_color=GOLD,
            focused_border_color=GOLD,
            color=CREAM,
            label_style=ft.TextStyle(color=MUTED),
        )
        sections = [self._photo_picker(), name_field]
        for classification in self.store.classifications():
            sections.append(self._classification_editor(classification))
        self.paint(
            self.screen(
                *sections,
                ft.Button(
                    content="Guardar personaje",
                    icon=ft.Icons.SAVE,
                    bgcolor=GOLD,
                    color=WHITE,
                    on_click=self._save_character,
                ),
                ft.Container(height=24),
            ),
            title="Editar" if self.form_id else "Nuevo personaje",
            on_back=self.show_characters,
        )

    def _photo_picker(self) -> ft.Control:
        return ft.Container(
            bgcolor=CARD,
            border_radius=20,
            padding=12,
            on_click=self._pick_image,
            content=ft.Column(
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        height=180,
                        border_radius=16,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=portrait(self.form_image, height=180),
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.PHOTO_CAMERA, color=GOLD),
                            ft.Text("Toca para elegir imagen", color=GOLD),
                        ],
                    ),
                ],
            ),
        )

    async def _pick_image(self, _e) -> None:
        files = await self.file_picker.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.IMAGE,
            with_data=True,
        )
        if not files:
            return
        chosen = files[0]
        source = Path(chosen.path) if chosen.path else Path(chosen.name or "personaje.jpg")
        stored = save_image(source, raw=chosen.bytes)
        self.form_image = str(stored)
        self._render_character_form()

    def _classification_editor(self, classification: Classification) -> ft.Control:
        selected = self.form_traits.setdefault(classification.id, set())
        chips = []
        for value in self.store.values(classification.id):
            is_selected = value.id in selected
            chips.append(
                ft.Chip(
                    label=ft.Text(
                        value.name,
                        color=WHITE if is_selected else CREAM,
                        weight=ft.FontWeight.W_600,
                    ),
                    selected=is_selected,
                    selected_color=GOLD,
                    bgcolor=CARD_SOFT,
                    check_color=WHITE,
                    show_checkmark=True,
                    on_select=lambda e, item=classification, val=value: self._toggle_form_value(item, val),
                )
            )
        return ft.Container(
            bgcolor=CARD,
            border_radius=18,
            padding=14,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(CLASS_ICONS.get(classification.slug, ft.Icons.LABEL), color=GOLD),
                                    ft.Text(classification.name, color=CREAM, weight=ft.FontWeight.W_700),
                                ]
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ADD_CIRCLE,
                                icon_color=GOLD,
                                tooltip="Crear elemento",
                                on_click=lambda e, item=classification: self._prompt_new_value(
                                    item, on_saved=lambda created: self._on_value_created(item, created)
                                ),
                            ),
                        ],
                    ),
                    hint("Puedes elegir varios." if classification.multi_select else "Elige uno, o crea uno nuevo."),
                    ft.Row(wrap=True, spacing=8, run_spacing=8, controls=chips),
                ],
            ),
        )

    def _toggle_form_value(self, classification: Classification, value: ClassificationValue) -> None:
        selected = self.form_traits.setdefault(classification.id, set())
        if classification.multi_select:
            if value.name.lower() == "ninguno":
                selected.clear()
                selected.add(value.id)
            else:
                none_ids = {
                    item.id
                    for item in self.store.values(classification.id)
                    if item.name.lower() == "ninguno"
                }
                selected.difference_update(none_ids)
                if value.id in selected:
                    selected.remove(value.id)
                else:
                    selected.add(value.id)
        else:
            if value.id in selected and len(selected) == 1:
                selected.clear()
            else:
                selected.clear()
                selected.add(value.id)
        self._render_character_form()

    def _on_value_created(self, classification: Classification, value: ClassificationValue) -> None:
        selected = self.form_traits.setdefault(classification.id, set())
        if not classification.multi_select:
            selected.clear()
        selected.add(value.id)
        self._render_character_form()

    def _prompt_new_value(self, classification: Classification, on_saved) -> None:
        field = ft.TextField(
            label=f"Nuevo en {classification.name}",
            autofocus=True,
            hint_text="Ej. Blanco",
            color=NAVY,
            bgcolor="#F7F8FA",
            border_color=GOLD,
            focused_border_color=GOLD_DARK,
            cursor_color=NAVY,
            label_style=ft.TextStyle(color="#5A6B7A"),
        )

        def save(_e) -> None:
            try:
                created = self.store.add_value(classification.id, field.value or "")
            except ValueError as exc:
                self.toast(str(exc))
                return
            self.close_dialog()
            on_saved(created)

        self._alert(
            title="Nuevo elemento",
            message=f"Se agregará a {classification.name.lower()} y podrás usarlo en este y otros personajes.",
            tone="info",
            confirm_label="Crear",
            on_confirm=save,
            extra=field,
        )

    def _save_character(self, _e) -> None:
        value_ids: list[int] = []
        for selected in self.form_traits.values():
            value_ids.extend(selected)
        try:
            self.store.save_character(
                self.form_name,
                self.form_image,
                value_ids,
                character_id=self.form_id,
            )
        except ValueError as exc:
            self.toast(str(exc))
            return
        self.toast("Personaje guardado.")
        self.show_characters()

    def start_game(self) -> None:
        characters = self.store.characters()
        try:
            p1_board, p2_board = pick_boards([item.id for item in characters])
        except GameError as exc:
            self.toast(str(exc))
            return
        self.game = GameSession(p1_board=p1_board, p2_board=p2_board)
        self.show_secret_select(1)

    def show_pass(self, to_player: int, then) -> None:
        self.pass_to = to_player
        self.after_pass = then
        color = TEAL if to_player == 1 else CORAL
        self.paint(
            ft.SafeArea(
                expand=True,
                content=ft.Container(
                    expand=True,
                    bgcolor=NAVY_DEEP,
                    padding=28,
                    content=ft.Column(
                        expand=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=18,
                        controls=[
                            ft.Icon(ft.Icons.PHONELINK_SETUP, size=72, color=color),
                            ft.Text(
                                f"Pasa el celular al jugador {to_player}",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                                color=CREAM,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                "Así el otro no ve el tablero ni el personaje secreto.",
                                color=MUTED,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Container(height=12),
                            ft.Button(
                                content=f"Ya soy el jugador {to_player}",
                                bgcolor=color,
                                color=NAVY_DEEP,
                                on_click=lambda e: self.after_pass(),
                            ),
                            ft.TextButton("Salir de la partida", on_click=lambda e: self.show_home()),
                        ],
                    ),
                ),
            )
        )

    def show_secret_select(self, player: int) -> None:
        if self.game is None:
            self.show_home()
            return
        self.pick_player = player
        self.picked_id = self.game.secret_of(player)
        self._render_secret_select()

    def _render_secret_select(self) -> None:
        game = self.game
        if game is None:
            return
        by_id = {item.id: item for item in self.store.characters()}
        board = [by_id[cid] for cid in game.board_for(self.pick_player) if cid in by_id]
        self.paint(
            ft.SafeArea(
                expand=True,
                content=ft.Container(
                    expand=True,
                    bgcolor=NAVY,
                    padding=12,
                    content=ft.Column(
                        expand=True,
                        spacing=10,
                        controls=[
                            ft.Text(
                                f"Jugador {self.pick_player}, elige tu personaje secreto",
                                color=CREAM,
                                size=18,
                                weight=ft.FontWeight.W_700,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            hint("Nadie más debe ver esta pantalla. Luego confirma y pasa el celular."),
                            ft.GridView(
                                expand=True,
                                runs_count=4,
                                max_extent=110,
                                child_aspect_ratio=0.72,
                                spacing=8,
                                run_spacing=8,
                                controls=[
                                    character_card(
                                        character,
                                        selected=self.picked_id == character.id,
                                        on_click=lambda e, cid=character.id: self._choose_secret(cid),
                                    )
                                    for character in board
                                ],
                            ),
                            ft.Button(
                                content="Confirmar personaje",
                                icon=ft.Icons.CHECK,
                                bgcolor=GOLD,
                                color=WHITE,
                                disabled=self.picked_id is None,
                                on_click=self._confirm_secret,
                            ),
                        ],
                    ),
                ),
            ),
            title=f"Jugador {self.pick_player}",
            on_back=self.show_home,
        )

    def _choose_secret(self, character_id: int) -> None:
        self.picked_id = character_id
        self._render_secret_select()

    def _confirm_secret(self, _e) -> None:
        if self.game is None or self.picked_id is None:
            self.toast("Selecciona un personaje.")
            return
        try:
            self.game.set_secret(self.pick_player, self.picked_id)
        except GameError as exc:
            self.toast(str(exc))
            return
        if self.pick_player == 1:
            self.show_pass(2, lambda: self.show_secret_select(2))
        else:
            self.show_pass(1, self.show_play)

    def show_play(self) -> None:
        game = self.game
        if game is None:
            self.show_home()
            return
        if game.winner is not None:
            self.show_winner()
            return
        by_id = {item.id: item for item in self.store.characters()}
        board = [by_id[cid] for cid in game.target_board() if cid in by_id]
        player = game.current_player
        color = TEAL if player == 1 else CORAL
        if game.mode == "discard":
            status = "Modo descarte: toca para tachar o volver a activar."
        elif game.mode == "guess":
            status = "Modo adivinar: toca el personaje que crees que es."
        elif game.asked_this_turn:
            status = "Ya preguntaste. Descarta si quieres y pulsa Listo."
        else:
            status = "Pregunta una clasificación, descarta a criterio y pulsa Listo."

        chips = []
        for classification in self.store.classifications():
            remaining = game.available_values([item.id for item in self.store.values(classification.id)])
            chips.append(
                ft.Chip(
                    label=classification.name,
                    leading=ft.Icon(CLASS_ICONS.get(classification.slug, ft.Icons.LABEL), size=16),
                    bgcolor=CARD_SOFT,
                    disabled=game.asked_this_turn or not remaining,
                    on_click=lambda e, item=classification: self._open_ask_dialog(item),
                )
            )

        answer_banner = []
        if game.last_answer:
            hit = bool(game.last_hit)
            answer_banner.append(
                ft.Container(
                    bgcolor=WHITE,
                    border_radius=14,
                    padding=12,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE if hit else ft.Icons.CANCEL,
                                color=SUCCESS if hit else DANGER,
                                size=28,
                            ),
                            ft.Column(
                                spacing=2,
                                expand=True,
                                controls=[
                                    ft.Text(
                                        "Acertaste" if hit else "No acertaste",
                                        color=SUCCESS if hit else DANGER,
                                        weight=ft.FontWeight.BOLD,
                                        size=16,
                                    ),
                                    ft.Text(
                                        game.last_answer,
                                        color=NAVY,
                                        weight=ft.FontWeight.W_600,
                                        size=13,
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
            )

        self.paint(
            ft.Container(
                expand=True,
                width=float("inf"),
                bgcolor=NAVY,
                content=ft.Column(
                    expand=True,
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        ft.Container(
                            bgcolor=NAVY_DEEP,
                            padding=12,
                            width=float("inf"),
                            content=ft.Column(
                                spacing=6,
                                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                controls=[
                                    ft.Text(
                                        f"Turno del jugador {player}",
                                        color=color,
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Text(
                                        status,
                                        color=MUTED,
                                        size=12,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    *answer_banner,
                                ],
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            padding=10,
                            width=float("inf"),
                            content=ft.GridView(
                                expand=True,
                                runs_count=4,
                                max_extent=110,
                                child_aspect_ratio=0.72,
                                spacing=8,
                                run_spacing=8,
                                controls=[
                                    character_card(
                                        character,
                                        discarded=game.is_discarded(character.id),
                                        on_click=lambda e, cid=character.id: self._on_board_tap(cid),
                                    )
                                    for character in board
                                ],
                            ),
                        ),
                        ft.Container(
                            bgcolor=NAVY_DEEP,
                            padding=10,
                            width=float("inf"),
                            content=ft.Column(
                                spacing=8,
                                tight=True,
                                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                controls=[
                                    ft.Row(
                                        wrap=True,
                                        spacing=6,
                                        run_spacing=6,
                                        controls=chips,
                                    ),
                                    ft.Row(
                                        spacing=6,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.Button(
                                                content=ft.Text(
                                                    "Descartar",
                                                    color=WHITE if game.mode == "discard" else CREAM,
                                                    weight=ft.FontWeight.W_700,
                                                    size=14,
                                                    max_lines=1,
                                                ),
                                                expand=5,
                                                icon=ft.Icons.BLOCK,
                                                icon_color=WHITE if game.mode == "discard" else CREAM,
                                                bgcolor=GOLD if game.mode == "discard" else CARD,
                                                style=ft.ButtonStyle(
                                                    padding=ft.Padding.symmetric(horizontal=8, vertical=12)
                                                ),
                                                on_click=lambda e: self._set_mode("discard"),
                                            ),
                                            ft.Button(
                                                content=ft.Text(
                                                    "Adivinar",
                                                    color=WHITE if game.mode == "guess" else CREAM,
                                                    weight=ft.FontWeight.W_700,
                                                    size=14,
                                                    max_lines=1,
                                                ),
                                                expand=5,
                                                icon=ft.Icons.LIGHTBULB,
                                                icon_color=WHITE if game.mode == "guess" else CREAM,
                                                bgcolor=GOLD if game.mode == "guess" else CARD,
                                                style=ft.ButtonStyle(
                                                    padding=ft.Padding.symmetric(horizontal=8, vertical=12)
                                                ),
                                                on_click=lambda e: self._set_mode("guess"),
                                            ),
                                            ft.Button(
                                                content=ft.Text(
                                                    "Listo",
                                                    color=WHITE,
                                                    weight=ft.FontWeight.W_700,
                                                    size=14,
                                                    max_lines=1,
                                                ),
                                                expand=4,
                                                icon=ft.Icons.DONE,
                                                icon_color=WHITE,
                                                bgcolor=TEAL,
                                                style=ft.ButtonStyle(
                                                    padding=ft.Padding.symmetric(horizontal=8, vertical=12)
                                                ),
                                                on_click=self._end_turn,
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            ),
            title="Partida",
            on_back=self._confirm_exit_game,
        )

    def _set_mode(self, mode: str) -> None:
        if self.game is None:
            return
        self.game.mode = "none" if self.game.mode == mode else mode
        self.show_play()

    def _on_board_tap(self, character_id: int) -> None:
        game = self.game
        if game is None:
            return
        if game.mode == "discard":
            game.toggle_discard(character_id)
            self.show_play()
            return
        if game.mode == "guess":
            self._confirm_guess(character_id)

    def _open_ask_dialog(self, classification: Classification) -> None:
        game = self.game
        if game is None:
            return
        values = [
            item
            for item in self.store.values(classification.id)
            if item.id in game.available_values([item.id for item in self.store.values(classification.id)])
        ]
        if not values:
            self.toast("Ya preguntaste todos los elementos de esta clasificación.")
            return
        options = [
            ft.Button(
                content=ft.Text(value.name, color=WHITE, weight=ft.FontWeight.W_700),
                bgcolor=GOLD,
                color=WHITE,
                style=ft.ButtonStyle(
                    padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                    shape=ft.RoundedRectangleBorder(radius=20),
                ),
                on_click=lambda e, val=value: self._ask_value(classification, val),
            )
            for value in values
        ]
        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                bgcolor=WHITE,
                shape=ft.RoundedRectangleBorder(radius=18),
                icon=ft.Icon(
                    CLASS_ICONS.get(classification.slug, ft.Icons.HELP),
                    color=GOLD,
                    size=36,
                ),
                title=ft.Text(
                    f'Elige lo que deseas preguntar sobre "{classification.name}"',
                    color=NAVY,
                    weight=ft.FontWeight.W_700,
                    size=16,
                    text_align=ft.TextAlign.CENTER,
                ),
                content=ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=options,
                ),
                actions=[
                    ft.Button(
                        content="Cancelar",
                        bgcolor=WHITE,
                        color=NAVY,
                        style=ft.ButtonStyle(
                            side=ft.BorderSide(1, "#C5D0DC"),
                            shape=ft.RoundedRectangleBorder(radius=12),
                        ),
                        on_click=self.close_dialog,
                    )
                ],
            )
        )

    def _ask_value(self, classification: Classification, value: ClassificationValue) -> None:
        game = self.game
        if game is None:
            return
        secret = self.store.character(game.target_secret())
        if secret is None:
            self.toast("No se encontró el personaje secreto.")
            return
        owned = secret.traits.get(classification.id, set())
        try:
            result = game.ask(
                value.id,
                owned_value_ids=owned,
                slug=classification.slug,
                value_name=value.name,
                multi_select=classification.multi_select,
            )
        except (AlreadyAskedError, AlreadyAskedThisTurnError, GameError) as exc:
            self.close_dialog()
            self.toast(str(exc))
            return
        self.close_dialog()
        hit = result.has_trait
        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                bgcolor=WHITE,
                shape=ft.RoundedRectangleBorder(radius=18),
                title=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE if hit else ft.Icons.CANCEL,
                            color=SUCCESS if hit else DANGER,
                            size=28,
                        ),
                        ft.Text(
                            "Acertaste" if hit else "No acertaste",
                            color=SUCCESS if hit else DANGER,
                            weight=ft.FontWeight.BOLD,
                            size=18,
                        ),
                    ],
                ),
                content=ft.Text(
                    result.message,
                    size=15,
                    color=NAVY,
                    text_align=ft.TextAlign.CENTER,
                ),
                actions_alignment=ft.MainAxisAlignment.CENTER,
                actions=[
                    ft.Button(
                        content="Entendido",
                        bgcolor=GOLD,
                        color=WHITE,
                        on_click=lambda e: self._after_answer(),
                    )
                ],
            )
        )

    def _after_answer(self) -> None:
        self.close_dialog()
        self.show_play()

    def _confirm_guess(self, character_id: int) -> None:
        character = self.store.character(character_id)
        if character is None:
            return
        self._alert(
            title="¿Adivinar este personaje?",
            message=f"Si {character.name} no es el personaje secreto, pierdes el turno y le toca al otro jugador.",
            tone="warning",
            confirm_label="Adivinar",
            on_confirm=lambda e, cid=character_id: self._do_guess(cid),
        )

    def _do_guess(self, character_id: int) -> None:
        game = self.game
        if game is None:
            return
        self.close_dialog()
        try:
            won = game.guess(character_id)
        except GameError as exc:
            self.toast(str(exc))
            return
        if won:
            self.show_winner()
            return
        self._alert(
            title="No era ese personaje",
            message="Fallaste. Pierdes el turno. Pasa el celular al otro jugador.",
            tone="danger",
            confirm_label="Pasar el celular",
            on_confirm=lambda e: self._after_failed_guess(),
            cancel_label=None,
        )

    def _after_failed_guess(self) -> None:
        self.close_dialog()
        if self.game is None:
            self.show_home()
            return
        nxt = self.game.current_player
        self.show_pass(nxt, self.show_play)

    def _end_turn(self, _e) -> None:
        if self.game is None:
            return
        self.game.end_turn()
        nxt = self.game.current_player
        self.show_pass(nxt, self.show_play)

    def _confirm_exit_game(self) -> None:
        self._alert(
            title="Salir de la partida",
            message="Si sales ahora se perderá el progreso de esta partida. Los personajes creados se conservan.",
            tone="danger",
            confirm_label="Salir",
            on_confirm=lambda e: (self.close_dialog(), self.show_home()),
            cancel_label="Seguir jugando",
        )

    def show_winner(self) -> None:
        game = self.game
        if game is None or game.winner is None:
            self.show_home()
            return
        secret_id = game.p2_secret if game.winner == 1 else game.p1_secret
        secret = self.store.character(secret_id) if secret_id else None
        self.paint(
            self.screen(
                ft.Container(height=12),
                ft.Icon(ft.Icons.EMOJI_EVENTS, size=72, color=GOLD),
                ft.Text(
                    f"¡Jugador {game.winner} gana!",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=GOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text("El personaje secreto era:", color=MUTED, text_align=ft.TextAlign.CENTER),
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=ft.Container(
                        width=180,
                        height=220,
                        border_radius=20,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                portrait(secret.image_path if secret else "", height=170),
                                ft.Text(
                                    secret.name if secret else "Desconocido",
                                    color=CREAM,
                                    text_align=ft.TextAlign.CENTER,
                                    weight=ft.FontWeight.W_700,
                                ),
                            ],
                        ),
                    ),
                ),
                ft.Button(
                    content="Jugar de nuevo",
                    icon=ft.Icons.REPLAY,
                    bgcolor=GOLD,
                    color=WHITE,
                    on_click=lambda e: self.start_game(),
                ),
                ft.TextButton("Volver al inicio", on_click=lambda e: self.show_home()),
            ),
            title="Fin de la partida",
        )
