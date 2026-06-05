"""Load portfolio content from per-section TOML files into typed dataclasses.

Copy is split across ``content/`` so each part of the site lives in its own file:

    content/home.toml          profile (bio) + the home-screen menu
    content/creations.toml     the Creations section
    content/reflections.toml   the Reflections section
    content/contacts.toml      the Contacts links

The home menu drives everything: each entry with ``kind = "listing"`` loads
``content/<key>.toml`` as a section, and the ``kind = "contacts"`` entry loads
``content/<key>.toml`` as a list of links. Adding a new section is just a new
menu entry plus a matching file — no code changes. ASCII art lives in ``art/``.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
CONTENT_DIR = PKG_DIR / "content"
ART_DIR = PKG_DIR / "art"


@dataclass
class Item:
    title: str
    body: list[str] = field(default_factory=list)
    url: str | None = None
    meta: str | None = None


@dataclass
class Group:
    label: str
    items: list[Item]


@dataclass
class Section:
    key: str
    title: str
    groups: list[Group]

    @property
    def items(self) -> list[Item]:
        """All items across groups, in display order."""
        return [item for group in self.groups for item in group.items]


@dataclass
class Contact:
    label: str
    value: str
    url: str | None = None


@dataclass
class MenuEntry:
    label: str
    kind: str  # "listing" | "contacts"
    key: str


@dataclass
class Profile:
    handle: str
    name_art: str
    portrait: str
    intro: list[str]
    about: list[str]
    closing: list[str]


@dataclass
class Content:
    profile: Profile
    sections: dict[str, Section]
    contacts: list[Contact]
    menu: list[MenuEntry]


def _read_art(name: str, fallback: str = "") -> str:
    path = ART_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8").rstrip("\n")
    return fallback


def _load_toml(path: Path) -> dict:
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def _normalize_url(value: str) -> str:
    """Turn a display value into an openable URL.

    'github.com/me' -> 'https://github.com/me', 'me@x.com' -> 'mailto:me@x.com'.
    """
    v = value.strip()
    if v.startswith(("http://", "https://", "mailto:")):
        return v
    if "@" in v and "/" not in v:
        return f"mailto:{v}"
    return f"https://{v}"


def _build_section(key: str, raw: dict) -> Section:
    groups: list[Group] = []
    for graw in raw.get("groups", []):
        items = [
            Item(
                title=iraw["title"],
                body=iraw.get("body", []),
                url=iraw.get("url"),
                meta=iraw.get("meta"),
            )
            for iraw in graw.get("items", [])
        ]
        groups.append(Group(label=graw.get("label", ""), items=items))
    return Section(key=key, title=raw.get("title", key.title()), groups=groups)


def load_content(content_dir: Path | None = None) -> Content:
    base = content_dir or CONTENT_DIR

    home = _load_toml(base / "home.toml")

    p = home.get("profile", {})
    handle = p.get("handle", "you")
    profile = Profile(
        handle=handle,
        name_art=_read_art("name.txt", handle),
        portrait=_read_art("portrait.txt", ""),
        intro=p.get("intro", []),
        about=p.get("about", []),
        closing=p.get("closing", []),
    )

    menu = [
        MenuEntry(label=m["label"], kind=m["kind"], key=m["key"])
        for m in home.get("menu", [])
    ]

    # Each menu entry points at its own file in the same directory.
    sections: dict[str, Section] = {}
    contacts: list[Contact] = []
    for entry in menu:
        path = base / f"{entry.key}.toml"
        if not path.exists():
            continue
        raw = _load_toml(path)
        if entry.kind == "contacts":
            contacts = [
                Contact(
                    label=c["label"],
                    value=c["value"],
                    url=c.get("url") or _normalize_url(c["value"]),
                )
                for c in raw.get("contacts", [])
            ]
        else:
            sections[entry.key] = _build_section(entry.key, raw)

    return Content(profile=profile, sections=sections, contacts=contacts, menu=menu)


_cache: Content | None = None


def get_content() -> Content:
    """Return the parsed content, loading and caching it on first use."""
    global _cache
    if _cache is None:
        _cache = load_content()
    return _cache
