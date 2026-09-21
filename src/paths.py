from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def storage_dir() -> Path:
    env = os.environ.get("FLET_APP_STORAGE_DATA")
    base = Path(env) if env else project_root() / "data"
    images = base / "images"
    images.mkdir(parents=True, exist_ok=True)
    return base


def images_dir() -> Path:
    folder = storage_dir() / "images"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def db_path() -> Path:
    return storage_dir() / "me_ubicas.db"


def demo_images_dir() -> Path:
    return project_root() / "Imagenes"
