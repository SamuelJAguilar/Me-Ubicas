from __future__ import annotations

from dataclasses import dataclass, field
import random

MAX_BOARD_SIZE = 20


class GameError(Exception):
    pass


class AlreadyAskedError(GameError):
    pass


class AlreadyAskedThisTurnError(GameError):
    pass


def pick_boards(
    character_ids: list[int],
    max_size: int = MAX_BOARD_SIZE,
    rng: random.Random | None = None,
) -> tuple[list[int], list[int]]:
    if len(character_ids) < 2:
        raise GameError("Se necesitan al menos 2 personajes para jugar.")
    rng = rng or random.Random()
    ids = list(character_ids)
    if len(ids) <= max_size:
        p1 = ids[:]
        p2 = ids[:]
        rng.shuffle(p1)
        rng.shuffle(p2)
        return p1, p2
    return rng.sample(ids, max_size), rng.sample(ids, max_size)


def character_has_value(
    owned_value_ids: set[int],
    value_id: int,
    *,
    multi_select: bool,
    value_name: str,
) -> bool:
    if value_id in owned_value_ids:
        return True
    if multi_select and value_name.strip().lower() == "ninguno" and not owned_value_ids:
        return True
    return False


def format_answer(slug: str, value_name: str, has_it: bool) -> str:
    value = value_name.strip().lower()
    yes_no = ("sí", "no") if has_it else ("no", "sí")

    if slug == "sexo" or slug == "edad":
        verb = "sí es" if has_it else "no es"
        return f"El personaje {verb} {value}."

    if slug == "pelo":
        return f"El personaje {yes_no[0]} tiene pelo {value}."
    if slug == "piel":
        return f"El personaje {yes_no[0]} tiene piel {value}."
    if slug == "ojos":
        return f"El personaje {yes_no[0]} tiene ojos {value}."
    if slug == "bello_facial":
        if value == "ninguno":
            return f"El personaje {'no tiene' if has_it else 'sí tiene'} bello facial."
        return f"El personaje {yes_no[0]} tiene {value}."
    if slug == "accesorios":
        if value == "ninguno":
            return f"El personaje {'no tiene' if has_it else 'sí tiene'} accesorios."
        return f"El personaje {yes_no[0]} tiene {value}."

    return f"El personaje {yes_no[0]} tiene {value}."


@dataclass
class AskResult:
    has_trait: bool
    message: str
    value_id: int


@dataclass
class GameSession:
    p1_board: list[int]
    p2_board: list[int]
    p1_secret: int | None = None
    p2_secret: int | None = None
    current_player: int = 1
    p1_discarded: set[int] = field(default_factory=set)
    p2_discarded: set[int] = field(default_factory=set)
    p1_asked: set[int] = field(default_factory=set)
    p2_asked: set[int] = field(default_factory=set)
    asked_this_turn: bool = False
    mode: str = "none"
    last_answer: str | None = None
    last_hit: bool | None = None
    winner: int | None = None

    def board_for(self, player: int) -> list[int]:
        return self.p1_board if player == 1 else self.p2_board

    def secret_of(self, player: int) -> int | None:
        return self.p1_secret if player == 1 else self.p2_secret

    def set_secret(self, player: int, character_id: int) -> None:
        board = self.board_for(player)
        if character_id not in board:
            raise GameError("Ese personaje no está en tu lista.")
        if player == 1:
            self.p1_secret = character_id
        else:
            self.p2_secret = character_id

    def target_board(self) -> list[int]:
        return self.p2_board if self.current_player == 1 else self.p1_board

    def target_secret(self) -> int:
        secret = self.p2_secret if self.current_player == 1 else self.p1_secret
        if secret is None:
            raise GameError("El otro jugador aún no elige personaje.")
        return secret

    def discarded(self) -> set[int]:
        return self.p1_discarded if self.current_player == 1 else self.p2_discarded

    def asked_values(self) -> set[int]:
        return self.p1_asked if self.current_player == 1 else self.p2_asked

    def toggle_discard(self, character_id: int) -> None:
        if character_id not in self.target_board():
            raise GameError("Ese personaje no está en el tablero.")
        discarded = self.discarded()
        if character_id in discarded:
            discarded.remove(character_id)
        else:
            discarded.add(character_id)

    def is_discarded(self, character_id: int) -> bool:
        return character_id in self.discarded()

    def available_values(self, value_ids: list[int]) -> list[int]:
        asked = self.asked_values()
        return [value_id for value_id in value_ids if value_id not in asked]

    def ask(
        self,
        value_id: int,
        *,
        owned_value_ids: set[int],
        slug: str,
        value_name: str,
        multi_select: bool,
    ) -> AskResult:
        if self.winner is not None:
            raise GameError("La partida ya terminó.")
        if self.asked_this_turn:
            raise AlreadyAskedThisTurnError("Ya preguntaste en este turno.")
        if value_id in self.asked_values():
            raise AlreadyAskedError("Esa característica ya se preguntó.")

        has_it = character_has_value(
            owned_value_ids,
            value_id,
            multi_select=multi_select,
            value_name=value_name,
        )
        message = format_answer(slug, value_name, has_it)
        self.asked_values().add(value_id)
        self.asked_this_turn = True
        self.last_answer = message
        self.last_hit = has_it
        self.mode = "none"
        return AskResult(has_trait=has_it, message=message, value_id=value_id)

    def guess(self, character_id: int) -> bool:
        if self.winner is not None:
            raise GameError("La partida ya terminó.")
        if character_id not in self.target_board():
            raise GameError("Ese personaje no está en el tablero.")
        if character_id == self.target_secret():
            self.winner = self.current_player
            self.mode = "none"
            return True
        self.end_turn()
        return False

    def end_turn(self) -> None:
        if self.winner is not None:
            return
        self.asked_this_turn = False
        self.last_answer = None
        self.last_hit = None
        self.mode = "none"
        self.current_player = 2 if self.current_player == 1 else 1
