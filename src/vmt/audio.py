from __future__ import annotations

import re
import subprocess
from pathlib import Path


class AudioError(Exception):
    """User-presentable problem with an input file."""


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def duration(path: Path) -> float:
    r = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
              "-of", "default=nw=1:nk=1", str(path)])
    try:
        return float(r.stdout.strip())
    except ValueError:
        raise AudioError("I couldn't read that audio file.") from None


def check_limits(path: Path, max_minutes: float, max_mb: float) -> float:
    size_mb = path.stat().st_size / 1_000_000
    if size_mb > max_mb:
        raise AudioError(f"File is too large ({size_mb:.0f} MB, limit {max_mb:.0f} MB).")
    d = duration(path)
    if d > max_minutes * 60:
        raise AudioError(f"Audio is too long ({d / 60:.1f} min, limit {max_minutes:g} min).")
    return d


def to_wav(src: Path, dst: Path) -> Path:
    """Convert any input to 16 kHz mono 16-bit WAV."""
    r = _run(["ffmpeg", "-y", "-i", str(src), "-ac", "1", "-ar", "16000",
              "-c:a", "pcm_s16le", str(dst)])
    if r.returncode != 0:
        raise AudioError("I couldn't decode that audio file.")
    return dst


def find_silences(wav: Path, noise_db: int = -30, min_silence: float = 0.3) -> list[float]:
    """Midpoints of silent regions, in seconds."""
    r = _run(["ffmpeg", "-i", str(wav), "-af",
              f"silencedetect=noise={noise_db}dB:d={min_silence}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    return [(s + e) / 2 for s, e in zip(starts, ends)]


def plan_chunks(total: float, silences: list[float], max_len: float = 28.0,
                overlap: float = 0.5) -> list[tuple[float, float]]:
    """Return (start, end) windows each <= max_len, cut at silences where possible."""
    chunks: list[tuple[float, float]] = []
    start = 0.0
    while total - start > max_len:
        limit = start + max_len
        # latest silence that still leaves a chunk of at least a third of max_len
        cands = [s for s in silences if start + max_len / 3 <= s <= limit]
        cut = max(cands) if cands else limit
        chunks.append((start, min(cut + overlap, start + max_len)))
        start = cut
    chunks.append((start, total))
    return chunks


def cut(wav: Path, start: float, end: float, dst: Path) -> Path:
    r = _run(["ffmpeg", "-y", "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
              "-i", str(wav), "-c", "copy", str(dst)])
    if r.returncode != 0:
        raise AudioError("Failed to split audio.")
    return dst


def join_transcripts(parts: list[str], max_overlap_words: int = 6) -> str:
    """Join chunk transcripts, removing words repeated across the overlap."""
    out: list[str] = []
    for part in parts:
        words = part.split()
        if not words:
            continue
        n = min(max_overlap_words, len(out), len(words))
        for k in range(n, 0, -1):
            norm = lambda ws: [w.lower().strip(".,!?;:") for w in ws]
            if norm(out[-k:]) == norm(words[:k]):
                words = words[k:]
                break
        out.extend(words)
    return " ".join(out)
