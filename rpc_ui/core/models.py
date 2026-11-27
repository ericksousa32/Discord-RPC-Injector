"""Presence data model and conversion to the Discord ``SET_ACTIVITY`` payload."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, fields

from ..i18n import tr

TEXT_FIELDS = (
    "app_id", "details", "state",
    "large_key", "large_text", "small_key", "small_text",
    "btn1_label", "btn1_url", "btn2_label", "btn2_url",
    "party_size", "party_max", "party_id",
)


@dataclass
class Presence:
    app_id: str = ""
    details: str = ""
    state: str = ""
    large_key: str = ""
    large_text: str = ""
    small_key: str = ""
    small_text: str = ""
    btn1_label: str = ""
    btn1_url: str = ""
    btn2_label: str = ""
    btn2_url: str = ""
    party_size: str = ""
    party_max: str = ""
    party_id: str = ""
    show_elapsed: bool = True

    # ── Serialization (preset format in presets.json) ────────────
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Presence":
        kwargs = {}
        for f in fields(cls):
            if f.name not in data:
                continue
            value = data[f.name]
            kwargs[f.name] = bool(value) if f.name == "show_elapsed" else str(value or "")
        return cls(**kwargs)

    # ── Activity sent to Discord (empty fields are omitted) ────────────
    def build_activity(self, start_ts: int | None = None) -> dict:
        activity: dict = {}
        if d := self.details.strip():
            activity["details"] = d
        if s := self.state.strip():
            activity["state"] = s

        if self.show_elapsed:
            activity["timestamps"] = {"start": start_ts or int(time.time())}

        assets = {}
        for key, src in (("large_image", self.large_key), ("large_text", self.large_text),
                         ("small_image", self.small_key), ("small_text", self.small_text)):
            if v := src.strip():
                assets[key] = v
        if assets:
            activity["assets"] = assets

        buttons = []
        for label, url in ((self.btn1_label, self.btn1_url), (self.btn2_label, self.btn2_url)):
            if label.strip() and url.strip():
                buttons.append({"label": label.strip(), "url": url.strip()})
        if buttons:
            activity["buttons"] = buttons

        try:
            if self.party_size.strip() and self.party_max.strip():
                ps, pm = int(self.party_size), int(self.party_max)
                pid = self.party_id.strip() or str(uuid.uuid4())
                activity["party"] = {"id": pid, "size": [ps, pm]}
        except (ValueError, TypeError):
            pass
        return activity

    def validate(self) -> list[tuple[tuple[str, ...], str]]:
        """Return ``(fields, message)`` for each problem; empty when everything is valid.

        ``fields`` names the form fields the problem concerns, so the UI can
        highlight them without matching on the message text.
        """
        problems = []
        if self.app_id.strip() and not self.app_id.strip().isdigit():
            problems.append((("app_id",), tr("validate.app_id")))
        for n, (label, url) in enumerate(((self.btn1_label, self.btn1_url),
                                          (self.btn2_label, self.btn2_url)), 1):
            fields = (f"btn{n}_label", f"btn{n}_url")
            if bool(label.strip()) != bool(url.strip()):
                problems.append((fields, tr("validate.button_incomplete", n=n)))
            elif url.strip() and not url.strip().startswith(("http://", "https://")):
                problems.append((fields, tr("validate.button_url", n=n)))
        party = ("party_size", "party_max")
        if self.party_size.strip() or self.party_max.strip():
            try:
                ps, pm = int(self.party_size), int(self.party_max)
                if ps < 0 or pm < ps:
                    problems.append((party, tr("validate.party_max")))
            except ValueError:
                problems.append((party, tr("validate.party_number")))
        return problems
