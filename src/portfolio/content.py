"""Load portfolio content from a TOML file into typed dataclasses.

All copy lives in ``content/portfolio.toml`` so the site can be updated without
touching any UI code. ASCII art lives in ``art/``.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
CONTENT_PATH = PKG_DIR / "content" / "portfolio.toml"
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


def load_content(path: Path | None = None) -> Content:
    with open(path or CONTENT_PATH, "rb") as fh:
        raw = tomllib.load(fh)

    p = raw.get("profile", {})
    handle = p.get("handle", "you")
    profile = Profile(
        handle=handle,
        name_art=_read_art("name.txt", handle),
        portrait=_read_art("portrait.txt", ""),
        intro=p.get("intro", []),
        about=p.get("about", []),
        closing=p.get("closing", []),
    )

    sections: dict[str, Section] = {}
    for key, sraw in raw.get("sections", {}).items():
        groups: list[Group] = []
        for graw in sraw.get("groups", []):
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
        sections[key] = Section(
            key=key, title=sraw.get("title", key.title()), groups=groups
        )

    contacts = [
        Contact(label=c["label"], value=c["value"]) for c in raw.get("contacts", [])
    ]
    menu = [
        MenuEntry(label=m["label"], kind=m["kind"], key=m["key"])
        for m in raw.get("menu", [])
    ]

    return Content(profile=profile, sections=sections, contacts=contacts, menu=menu)


_cache: Content | None = None


def get_content() -> Content:
    """Return the parsed content, loading and caching it on first use."""
    global _cache
    if _cache is None:
        _cache = load_content()
    return _cache
