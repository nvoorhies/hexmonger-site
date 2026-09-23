import shutil
from pathlib import Path

import pytest
from PIL import Image

from blog_editor.site import Site

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def site(tmp_path) -> Site:
    """A copy of the real site, without the editor's own files or any posts."""
    root = tmp_path / "site"
    shutil.copytree(REPO, root, ignore=shutil.ignore_patterns(".git", ".venv", "blog-editor", "blog", "_site"))
    (root / "blog-editor" / "posts").mkdir(parents=True)
    return Site(root)


def make_png(path: Path, size=(40, 30), color=(200, 120, 60)) -> Path:
    Image.new("RGB", size, color).save(path)
    return path
