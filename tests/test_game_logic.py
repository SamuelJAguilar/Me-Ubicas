from __future__ import annotations

import random
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(ROOT))

from game_logic import (
    AlreadyAskedError,
    AlreadyAskedThisTurnError,
    GameError,
    GameSession,
    character_has_value,
    format_answer,
    pick_boards,
)
from storage import Store


class PickBoardsTests(unittest.TestCase):
    def test_requires_two_characters(self):
        with self.assertRaises(GameError):
            pick_boards([1])

    def test_uses_all_when_under_limit(self):
        p1, p2 = pick_boards([1, 2, 3], rng=random.Random(0))
        self.assertCountEqual(p1, [1, 2, 3])
        self.assertCountEqual(p2, [1, 2, 3])

    def test_samples_twenty_when_there_are_more(self):
        ids = list(range(1, 30))
        p1, p2 = pick_boards(ids, rng=random.Random(1))
        self.assertEqual(len(p1), 20)
        self.assertEqual(len(p2), 20)
        self.assertTrue(set(p1).issubset(ids))
        self.assertTrue(set(p2).issubset(ids))


class AnswerFormatTests(unittest.TestCase):
    def test_hair_matches_requested_phrase(self):
        self.assertEqual(
            format_answer("pelo", "Blanco", False),
            "El personaje no tiene pelo blanco.",
        )
        self.assertEqual(
            format_answer("pelo", "Blanco", True),
            "El personaje sí tiene pelo blanco.",
        )

    def test_sex_uses_ser(self):
        self.assertEqual(format_answer("sexo", "Hombre", True), "El personaje sí es hombre.")


class TraitTests(unittest.TestCase):
    def test_empty_accessories_count_as_none(self):
        self.assertTrue(
            character_has_value(set(), 99, multi_select=True, value_name="Ninguno")
        )
        self.assertFalse(
            character_has_value(set(), 3, multi_select=True, value_name="Aretes")
        )


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.game = GameSession(
            p1_board=[1, 2, 3, 4],
            p2_board=[5, 6, 7, 8],
            p1_secret=2,
            p2_secret=6,
            current_player=1,
        )

    def test_ask_blocks_same_value_next_turn(self):
        result = self.game.ask(
            10,
            owned_value_ids={11},
            slug="pelo",
            value_name="Blanco",
            multi_select=False,
        )
        self.assertFalse(result.has_trait)
        self.assertIn(10, self.game.p1_asked)
        with self.assertRaises(AlreadyAskedThisTurnError):
            self.game.ask(
                12,
                owned_value_ids={11},
                slug="ojos",
                value_name="Azul",
                multi_select=False,
            )
        self.game.end_turn()
        self.assertEqual(self.game.current_player, 2)
        self.game.end_turn()
        with self.assertRaises(AlreadyAskedError):
            self.game.ask(
                10,
                owned_value_ids={11},
                slug="pelo",
                value_name="Blanco",
                multi_select=False,
            )

    def test_wrong_guess_loses_turn(self):
        self.assertFalse(self.game.guess(5))
        self.assertIsNone(self.game.winner)
        self.assertEqual(self.game.current_player, 2)

    def test_correct_guess_wins(self):
        self.assertTrue(self.game.guess(6))
        self.assertEqual(self.game.winner, 1)

    def test_discard_can_be_reverted_later(self):
        self.game.toggle_discard(5)
        self.assertTrue(self.game.is_discarded(5))
        self.game.end_turn()
        self.game.end_turn()
        self.game.toggle_discard(5)
        self.assertFalse(self.game.is_discarded(5))


class StoreTests(unittest.TestCase):
    def test_add_custom_hair_color_and_character(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "test.db", seed_demo=False)
            pelo = next(item for item in store.classifications() if item.slug == "pelo")
            blanco = store.add_value(pelo.id, "Blanco")
            negro = next(item for item in store.values(pelo.id) if item.name == "Negro")
            image = Path(tmp) / "face.jpg"
            image.write_bytes(b"fake")
            character_id = store.save_character("Kai", str(image), [blanco.id, negro.id])
            saved = store.character(character_id)
            self.assertIsNotNone(saved)
            self.assertEqual(saved.name, "Kai")
            self.assertIn(blanco.id, saved.value_ids())

    def test_lentes_lives_inside_accessories(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "test.db", seed_demo=False)
            slugs = [item.slug for item in store.classifications()]
            self.assertNotIn("lentes", slugs)
            accesorios = next(item for item in store.classifications() if item.slug == "accesorios")
            names = [item.name for item in store.values(accesorios.id)]
            self.assertIn("Lentes", names)

    def test_migrates_old_lentes_category(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "legacy.db"
            first = Store(db, seed_demo=False)
            with first.connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO classifications (slug, name, multi_select, sort_order)
                    VALUES ('lentes', 'Lentes', 0, 1)
                    """
                )
                lentes_id = cursor.lastrowid
                conn.execute(
                    "INSERT INTO classification_values (classification_id, name) VALUES (?, ?)",
                    (lentes_id, "Sí"),
                )
            migrated = Store(db, seed_demo=False)
            slugs = [item.slug for item in migrated.classifications()]
            self.assertNotIn("lentes", slugs)
            accesorios = next(item for item in migrated.classifications() if item.slug == "accesorios")
            self.assertIn("Lentes", [item.name for item in migrated.values(accesorios.id)])


if __name__ == "__main__":
    unittest.main()
