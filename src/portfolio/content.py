"""Load portfolio content from per-section TOML files into typed dataclasses.

Copy is split across ``data/`` so each part of the site lives in its own file:

    data/home.toml          profile, the "whoami" facts, and the tab bar (menu)
    data/experience.toml    a listing (list + detail pane)
    data/projects.toml      a listing
    data/skills.toml        grouped skill chips
    data/about.toml         a listing
    data/contacts.toml      contact links

The menu drives everything: each entry's ``kind`` (``listing``, ``skills`` or
``contacts``) decides how ``data/<key>.toml`` is read and which view renders it.
Adding a section is a new file plus one menu entry, with no code changes.
ASCII wordmarks live in ``art/``.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
CONTENT_DIR = PKG_DIR / "data"
ART_DIR = PKG_DIR / "art"


@dataclass
class Link:
    label: str
    url: str

    @property
    def text(self) -> str:
        """The URL as a person would write it: no scheme, no trailing slash."""
        for prefix in ("https://", "http://", "mailto:"):
            if self.url.startswith(prefix):
                return self.url[len(prefix):].rstrip("/")
        return self.url.rstrip("/")


@dataclass
class Item:
    title: str
    subtitle: str | None = None
    meta: str | None = None
    info: str | None = None
    body: list[str] = field(default_factory=list)
    bullets: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)


@dataclass
class Group:
    label: str
    items: list[Item]


@dataclass
class SkillGroup:
    label: str
    items: list[str]


@dataclass
class Contact:
    label: str
    value: str
    url: str


@dataclass
class Section:
    key: str
    kind: str  # "listing" | "skills" | "contacts"
    title: str
    intro: str = ""
    groups: list[Group] = field(default_factory=list)
    skills: list[SkillGroup] = field(default_factory=list)
    contacts: list[Contact] = field(default_factory=list)

    @property
    def items(self) -> list[Item]:
        """All listing items across groups, in display order."""
        return [item for group in self.groups for item in group.items]


@dataclass
class MenuEntry:
    label: str
    kind: str
    key: str


@dataclass
class Fact:
    key: str
    value: str


@dataclass
class Profile:
    handle: str
    host: str
    tagline: str
    city: str
    timezone: str
    ssh: str
    facts: list[Fact]
    name_art: str
    name_compact: str


@dataclass
class Content:
    profile: Profile
    sections: dict[str, Section]
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


def _build_listing(key: str, raw: dict) -> Section:
    groups: list[Group] = []
    for graw in raw.get("groups", []):
        items = [
            Item(
                title=iraw["title"],
                subtitle=iraw.get("subtitle"),
                meta=iraw.get("meta"),
                info=iraw.get("info"),
                body=iraw.get("body", []),
                bullets=iraw.get("bullets", []),
                tags=iraw.get("tags", []),
                links=[
                    Link(label=lraw["label"], url=_normalize_url(lraw["url"]))
                    for lraw in iraw.get("links", [])
                ],
            )
            for iraw in graw.get("items", [])
        ]
        groups.append(Group(label=graw.get("label", ""), items=items))
    return Section(key=key, kind="listing", title=raw.get("title", key), groups=groups)


def _build_skills(key: str, raw: dict) -> Section:
    skills = [
        SkillGroup(label=g["label"], items=g.get("items", []))
        for g in raw.get("groups", [])
    ]
    return Section(key=key, kind="skills", title=raw.get("title", key), skills=skills)


def _build_contacts(key: str, raw: dict) -> Section:
    contacts = [
        Contact(
            label=c["label"],
            value=c["value"],
            url=c.get("url") or _normalize_url(c["value"]),
        )
        for c in raw.get("contacts", [])
    ]
    return Section(
        key=key,
        kind="contacts",
        title=raw.get("title", key),
        intro=raw.get("intro", ""),
        contacts=contacts,
    )


_BUILDERS = {
    "listing": _build_listing,
    "skills": _build_skills,
    "contacts": _build_contacts,
}


def load_content(content_dir: Path | None = None) -> Content:
    base = content_dir or CONTENT_DIR

    home = _load_toml(base / "home.toml")

    p = home.get("profile", {})
    handle = p.get("handle", "you")
    profile = Profile(
        handle=handle,
        host=p.get("host", "portfolio"),
        tagline=p.get("tagline", ""),
        city=p.get("city", ""),
        timezone=p.get("timezone", ""),
        ssh=p.get("ssh", ""),
        facts=[Fact(key=f["key"], value=f["value"]) for f in home.get("facts", [])],
        name_art=_read_art("name.txt", handle),
        name_compact=_read_art("name_compact.txt", handle),
    )

    menu = [
        MenuEntry(label=m["label"], kind=m["kind"], key=m["key"])
        for m in home.get("menu", [])
    ]

    # Each menu entry points at its own file in the same directory.
    sections: dict[str, Section] = {}
    for entry in menu:
        path = base / f"{entry.key}.toml"
        builder = _BUILDERS.get(entry.kind)
        if builder is None or not path.exists():
            continue
        sections[entry.key] = builder(entry.key, _load_toml(path))

    return Content(profile=profile, sections=sections, menu=menu)


_cache: Content | None = None


def get_content() -> Content:
    """Return the parsed content, loading and caching it on first use."""
    global _cache
    if _cache is None:
        _cache = load_content()
    return _cache
