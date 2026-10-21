from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Result:
    language: str
    language_name: str
    engine: str
    duration_s: float
    transcript: str
    translation: str | None = None
    summary: str | None = None
    timings: dict[str, float] = field(default_factory=dict)


def fmt_duration(s: float) -> str:
    s = int(round(s))
    return f"{s // 60}:{s % 60:02d}"


def format_reply(r: Result) -> str:
    out = [f"🎙 Voicemail · {r.language_name} · {fmt_duration(r.duration_s)} · {r.engine}",
           "", "📝 Original", r.transcript or "(no speech detected)"]
    if r.translation:
        out += ["", "🇬🇧 English", r.translation]
    if r.summary:
        out += ["", "📌 Summary", r.summary]
    return "\n".join(out)


def split_message(text: str, limit: int = 4096) -> list[str]:
    """Split on paragraph/line/space boundaries to fit Telegram's size limit."""
    chunks = []
    while len(text) > limit:
        cut = max(text.rfind(sep, 0, limit) for sep in ("\n\n", "\n", " "))
        cut = cut if cut > limit // 2 else limit
        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    chunks.append(text)
    return chunks
