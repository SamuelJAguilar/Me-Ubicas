from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import sqlite3
from pathlib import Path
import shutil
import uuid

from models import Character, Classification, ClassificationValue
from paths import db_path, demo_images_dir, images_dir


DEFAULT_CLASSIFICATIONS = [
    ("ojos", "Ojos", False, 1, ["Café", "Azul", "Verde"]),
    ("pelo", "Pelo", False, 2, ["Negro", "Rubio"]),
    ("piel", "Piel", False, 3, ["Clara", "Media", "Oscura"]),
    ("sexo", "Sexo", False, 4, ["Hombre", "Mujer"]),
    ("edad", "Edad", False, 5, ["Joven", "Adulto", "Viejo"]),
    ("bello_facial", "Bello facial", False, 6, ["Ninguno", "Bigote", "Barba"]),
    (
        "accesorios",
        "Accesorios",
        True,
        7,
        ["Ninguno", "Aretes", "Collar", "Gorra", "Sombrero", "Pañuelo", "Parche", "Lentes"],
    ),
]


@dataclass(frozen=True)
class DemoCharacter:
    filename: str
    name: str
    traits: dict[str, list[str]]


DEMO_CHARACTERS = [
    DemoCharacter(
        "Goku.jpg",
        "Goku",
        {
            "ojos": ["Morado"],
            "pelo": ["Negro"],
            "piel": ["Media"],
            "sexo": ["Hombre"],
            "edad": ["Joven"],
            "bello_facial": ["Ninguno"],
            "accesorios": ["Ninguno"],
        },
    ),
    DemoCharacter(
        "Naruto.jpg",
        "Naruto",
        {
            "ojos": ["Azul"],
            "pelo": ["Rubio"],
            "piel": ["Clara"],
            "sexo": ["Hombre"],
            "edad": ["Joven"],
            "bello_facial": ["Ninguno"],
            "accesorios": ["Aretes", "Pañuelo"],
        },
    ),
    DemoCharacter(
        "Jack.jpg",
        "Jack",
        {
            "ojos": ["Azul"],
            "pelo": ["Negro"],
            "piel": ["Clara"],
            "sexo": ["Hombre"],
            "edad": ["Joven"],
            "bello_facial": ["Ninguno"],
            "accesorios": ["Sombrero", "Parche"],
        },
    ),
    DemoCharacter(
        "4.jpg",
        "Shiro",
        {
            "ojos": ["Morado"],
            "pelo": ["Blanco"],
            "piel": ["Clara"],
            "sexo": ["Hombre"],
            "edad": ["Joven"],
            "bello_facial": ["Ninguno"],
            "accesorios": ["Ninguno"],
        },
    ),
]


class Store:
    def __init__(self, path: Path | None = None, seed_demo: bool = True) -> None:
        self.path = path or db_path()
        self.seed_demo = seed_demo
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        self._seed()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    multi_select INTEGER NOT NULL DEFAULT 0,
                    sort_order INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS classification_values (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    classification_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    UNIQUE(classification_id, name),
                    FOREIGN KEY(classification_id) REFERENCES classifications(id)
                );
                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    image_path TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS character_traits (
                    character_id INTEGER NOT NULL,
                    value_id INTEGER NOT NULL,
                    PRIMARY KEY (character_id, value_id),
                    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE,
                    FOREIGN KEY(value_id) REFERENCES classification_values(id)
                );
                """
            )

    def _seed(self) -> None:
        with self.connect() as conn:
            existing = {
                row["slug"]: row["id"]
                for row in conn.execute("SELECT id, slug FROM classifications")
            }
            for slug, name, multi, order, values in DEFAULT_CLASSIFICATIONS:
                if slug in existing:
                    class_id = existing[slug]
                else:
                    cursor = conn.execute(
                        """
                        INSERT INTO classifications (slug, name, multi_select, sort_order)
                        VALUES (?, ?, ?, ?)
                        """,
                        (slug, name, int(multi), order),
                    )
                    class_id = cursor.lastrowid
                for value in values:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO classification_values (classification_id, name)
                        VALUES (?, ?)
                        """,
                        (class_id, value),
                    )
            self._migrate_lentes_into_accessories(conn)
            count = conn.execute("SELECT COUNT(*) AS n FROM characters").fetchone()["n"]
            if count == 0 and self.seed_demo:
                self._seed_demo_characters(conn)

    def _migrate_lentes_into_accessories(self, conn: sqlite3.Connection) -> None:
        lentes_row = conn.execute(
            "SELECT id FROM classifications WHERE slug = ?",
            ("lentes",),
        ).fetchone()
        if lentes_row is None:
            return
        lentes_id = lentes_row["id"]
        acc_row = conn.execute(
            "SELECT id FROM classifications WHERE slug = ?",
            ("accesorios",),
        ).fetchone()
        if acc_row is None:
            return
        acc_id = acc_row["id"]
        conn.execute(
            "INSERT OR IGNORE INTO classification_values (classification_id, name) VALUES (?, ?)",
            (acc_id, "Lentes"),
        )
        lentes_value = conn.execute(
            """
            SELECT id FROM classification_values
            WHERE classification_id = ? AND name = ? COLLATE NOCASE
            """,
            (acc_id, "Lentes"),
        ).fetchone()
        si_value = conn.execute(
            """
            SELECT id FROM classification_values
            WHERE classification_id = ? AND LOWER(name) IN ('sí', 'si')
            """,
            (lentes_id,),
        ).fetchone()
        ninguno = conn.execute(
            """
            SELECT id FROM classification_values
            WHERE classification_id = ? AND name = ? COLLATE NOCASE
            """,
            (acc_id, "Ninguno"),
        ).fetchone()
        if si_value and lentes_value:
            for row in conn.execute(
                "SELECT character_id FROM character_traits WHERE value_id = ?",
                (si_value["id"],),
            ).fetchall():
                if ninguno:
                    conn.execute(
                        "DELETE FROM character_traits WHERE character_id = ? AND value_id = ?",
                        (row["character_id"], ninguno["id"]),
                    )
                conn.execute(
                    "INSERT OR IGNORE INTO character_traits (character_id, value_id) VALUES (?, ?)",
                    (row["character_id"], lentes_value["id"]),
                )
        conn.execute(
            """
            DELETE FROM character_traits
            WHERE value_id IN (
                SELECT id FROM classification_values WHERE classification_id = ?
            )
            """,
            (lentes_id,),
        )
        conn.execute("DELETE FROM classification_values WHERE classification_id = ?", (lentes_id,))
        conn.execute("DELETE FROM classifications WHERE id = ?", (lentes_id,))

    def _seed_demo_characters(self, conn: sqlite3.Connection) -> None:
        source_dir = demo_images_dir()
        if not source_dir.exists():
            return
        for demo in DEMO_CHARACTERS:
            source = source_dir / demo.filename
            if not source.is_file():
                continue
            stored = copy_image(source)
            cursor = conn.execute(
                "INSERT INTO characters (name, image_path) VALUES (?, ?)",
                (demo.name, str(stored)),
            )
            character_id = cursor.lastrowid
            for slug, names in demo.traits.items():
                class_row = conn.execute(
                    "SELECT id FROM classifications WHERE slug = ?",
                    (slug,),
                ).fetchone()
                if class_row is None:
                    continue
                class_id = class_row["id"]
                for name in names:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO classification_values (classification_id, name)
                        VALUES (?, ?)
                        """,
                        (class_id, name),
                    )
                    value_row = conn.execute(
                        """
                        SELECT id FROM classification_values
                        WHERE classification_id = ? AND name = ? COLLATE NOCASE
                        """,
                        (class_id, name),
                    ).fetchone()
                    if value_row:
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO character_traits (character_id, value_id)
                            VALUES (?, ?)
                            """,
                            (character_id, value_row["id"]),
                        )

    def classifications(self) -> list[Classification]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, slug, name, multi_select, sort_order
                FROM classifications
                ORDER BY sort_order, id
                """
            ).fetchall()
        return [
            Classification(
                id=row["id"],
                slug=row["slug"],
                name=row["name"],
                multi_select=bool(row["multi_select"]),
                sort_order=row["sort_order"],
            )
            for row in rows
        ]

    def values(self, classification_id: int) -> list[ClassificationValue]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, classification_id, name
                FROM classification_values
                WHERE classification_id = ?
                ORDER BY id
                """,
                (classification_id,),
            ).fetchall()
        return [
            ClassificationValue(
                id=row["id"],
                classification_id=row["classification_id"],
                name=row["name"],
            )
            for row in rows
        ]

    def all_values(self) -> list[ClassificationValue]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, classification_id, name
                FROM classification_values
                ORDER BY id
                """
            ).fetchall()
        return [
            ClassificationValue(
                id=row["id"],
                classification_id=row["classification_id"],
                name=row["name"],
            )
            for row in rows
        ]

    def add_value(self, classification_id: int, name: str) -> ClassificationValue:
        clean = " ".join(name.split())
        if not clean:
            raise ValueError("Escribe un nombre para el nuevo elemento.")
        with self.connect() as conn:
            existing = conn.execute(
                """
                SELECT id, classification_id, name
                FROM classification_values
                WHERE classification_id = ? AND name = ? COLLATE NOCASE
                """,
                (classification_id, clean),
            ).fetchone()
            if existing:
                return ClassificationValue(
                    id=existing["id"],
                    classification_id=existing["classification_id"],
                    name=existing["name"],
                )
            cursor = conn.execute(
                "INSERT INTO classification_values (classification_id, name) VALUES (?, ?)",
                (classification_id, clean),
            )
            return ClassificationValue(
                id=cursor.lastrowid,
                classification_id=classification_id,
                name=clean,
            )

    def _traits_map(self, conn: sqlite3.Connection, character_id: int) -> dict[int, set[int]]:
        rows = conn.execute(
            """
            SELECT cv.classification_id, ct.value_id
            FROM character_traits ct
            JOIN classification_values cv ON cv.id = ct.value_id
            WHERE ct.character_id = ?
            """,
            (character_id,),
        ).fetchall()
        traits: dict[int, set[int]] = {}
        for row in rows:
            traits.setdefault(row["classification_id"], set()).add(row["value_id"])
        return traits

    def characters(self) -> list[Character]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, name, image_path FROM characters ORDER BY name COLLATE NOCASE"
            ).fetchall()
            return [
                Character(
                    id=row["id"],
                    name=row["name"],
                    image_path=row["image_path"],
                    traits=self._traits_map(conn, row["id"]),
                )
                for row in rows
            ]

    def character(self, character_id: int) -> Character | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id, name, image_path FROM characters WHERE id = ?",
                (character_id,),
            ).fetchone()
            if row is None:
                return None
            return Character(
                id=row["id"],
                name=row["name"],
                image_path=row["image_path"],
                traits=self._traits_map(conn, row["id"]),
            )

    def save_character(
        self,
        name: str,
        image_path: str,
        value_ids: list[int],
        character_id: int | None = None,
    ) -> int:
        clean = " ".join(name.split())
        if not clean:
            raise ValueError("El personaje necesita un nombre.")
        if not image_path:
            raise ValueError("Agrega una imagen del personaje.")
        with self.connect() as conn:
            if character_id is None:
                cursor = conn.execute(
                    "INSERT INTO characters (name, image_path) VALUES (?, ?)",
                    (clean, image_path),
                )
                character_id = cursor.lastrowid
            else:
                conn.execute(
                    "UPDATE characters SET name = ?, image_path = ? WHERE id = ?",
                    (clean, image_path, character_id),
                )
                conn.execute(
                    "DELETE FROM character_traits WHERE character_id = ?",
                    (character_id,),
                )
            for value_id in set(value_ids):
                conn.execute(
                    """
                    INSERT OR IGNORE INTO character_traits (character_id, value_id)
                    VALUES (?, ?)
                    """,
                    (character_id, value_id),
                )
        return character_id

    def delete_character(self, character_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM characters WHERE id = ?", (character_id,))


def copy_image(source: Path, raw: bytes | None = None) -> Path:
    suffix = source.suffix.lower() if source.suffix else ".jpg"
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}:
        suffix = ".jpg"
    destination = images_dir() / f"{uuid.uuid4().hex}{suffix}"
    if raw:
        destination.write_bytes(raw)
    else:
        shutil.copyfile(source, destination)
    return destination
