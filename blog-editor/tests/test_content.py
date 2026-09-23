import datetime as dt
import io

import pytest
from PIL import Image

from blog_editor.content import (ContentError, Meta, Store, format_markdown_file,
                                 parse_markdown_file, slugify)


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path)


def test_front_matter_round_trip_with_awkward_title():
    meta = Meta(title='Tides: a "how it works"', date="2026-09-23", summary="Water, mostly.")
    text = format_markdown_file(meta, "Body $x$ here.\n")
    assert text.startswith("---\ntitle: ")
    back, body = parse_markdown_file(text)
    assert back == meta and body == "Body $x$ here.\n"


def test_unquoted_yaml_date_is_read_as_a_string():
    meta, body = parse_markdown_file("---\ntitle: T\ndate: 2026-01-02\n---\n\nHi\n")
    assert meta.date == "2026-01-02" and body == "Hi\n"


def test_slugify():
    assert slugify("Sand, Water & Crème Brûlée!") == "sand-water-creme-brulee"
    assert slugify("???") == "untitled"


def test_create_makes_a_unique_draft(store):
    a = store.create("Hello world", today=dt.date(2026, 9, 23))
    b = store.create("Hello world")
    assert (a.slug, b.slug) == ("hello-world", "hello-world-2")
    assert store.status("hello-world") == "draft"
    assert store.load("hello-world").meta.date == "2026-09-23"


def test_draft_publish_change_discard_unpublish(store):
    p = store.create("Post")
    store.save_published(p.slug, p.meta, "v1")
    assert store.status(p.slug) == "published"
    assert not (store.folder(p.slug) / "draft.md").exists()
    store.save_draft(p.slug, p.meta, "v2")
    assert store.status(p.slug) == "changed"
    assert store.load(p.slug).body == "v2\n"  # the editor opens the draft
    assert store.read(p.slug, "post.md").body == "v1\n"
    assert store.discard_draft(p.slug).body == "v1\n"
    store.unpublish(p.slug)
    assert store.status(p.slug) == "draft" and store.load(p.slug).body == "v1\n"


def test_rename_only_before_publishing(store):
    p = store.create("Old name")
    store.rename(p.slug, "new-name")
    assert store.slugs() == ["new-name"]
    store.save_published("new-name", p.meta, "x")
    with pytest.raises(ContentError):
        store.rename("new-name", "other")


@pytest.mark.parametrize("bad", ["../etc", "UPPER", "a/b", "", "-x"])
def test_bad_slugs_are_refused(store, bad):
    with pytest.raises(ContentError):
        store.folder(bad)


def _png(size):
    out = io.BytesIO()
    Image.new("RGB", size, (10, 20, 30)).save(out, "PNG")
    return out.getvalue()


def test_upload_web_size_and_dedupe(store):
    p = store.create("Media")
    name = store.add_media(p.slug, "Big Shot.PNG", _png((3000, 1500)), web_size=True)
    assert name == "big-shot.webp"
    with Image.open(store.folder(p.slug) / name) as im:
        assert im.size == (1600, 800)
    assert store.add_media(p.slug, "small.png", _png((50, 50)), web_size=False) == "small.png"
    assert store.add_media(p.slug, "small.png", _png((50, 50)), web_size=False) == "small.png"  # same bytes
    assert store.add_media(p.slug, "small.png", _png((60, 60)), web_size=False) == "small-2.png"
    assert [m["name"] for m in store.media(p.slug)] == ["big-shot.webp", "small-2.png", "small.png"]


def test_upload_refuses_other_files(store):
    p = store.create("Media")
    with pytest.raises(ContentError):
        store.add_media(p.slug, "run.sh", b"#!/bin/sh", web_size=False)
    with pytest.raises(ContentError):
        store.media_path(p.slug, "draft.md")
