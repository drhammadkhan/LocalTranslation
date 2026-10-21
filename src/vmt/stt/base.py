from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Transcription:
    text: str
    language: str | None = None
    avg_prob: float | None = None


class STTEngine(ABC):
    name: str

    @abstractmethod
    def transcribe(self, wav: Path, language: str | None = None) -> Transcription:
        """Transcribe one 16 kHz mono WAV (<= engine's max window)."""

    def detect_language(self, wav: Path) -> str | None:
        return None

    max_window_s: float | None = None  # None = handles long audio itself
