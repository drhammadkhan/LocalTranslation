import subprocess
from pathlib import Path

import pytest

from vmt.config import Config
from vmt.pipeline import Pipeline
from vmt.stt.base import STTEngine, Transcription
from vmt.translate.base import Translator


def make_audio(path: Path, speech_s: list[float], gap_s: float = 0.8) -> Path:
    """Tone bursts separated by silence, as .ogg/opus like a WhatsApp voice note."""
    parts, labels = [], []
    for i, s in enumerate(speech_s):
        parts.append(f"sine=f=440:d={s}")
        parts.append(f"anullsrc=r=16000:cl=mono:d={gap_s}")
    n = len(parts)
    inputs = sum((["-f", "lavfi", "-i", p] for p in parts), [])
    graph = "".join(f"[{i}:a]" for i in range(n)) + f"concat=n={n}:v=0:a=1[o]"
    subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", graph, "-map", "[o]",
                    "-ar", "16000", "-ac", "1", str(path)], check=True, capture_output=True)
    return path


class FakeSTT(STTEngine):
    def __init__(self, name="whisper", lang="fr", text="bonjour tout le monde", window=None):
        self.name, self.lang, self.text, self.max_window_s = name, lang, text, window
        self.calls = []

    def detect_language(self, wav):
        return self.lang

    def transcribe(self, wav, language=None):
        self.calls.append(wav.name)
        return Transcription(self.text, language or self.lang)


class FakeTranslator(Translator):
    def translate(self, text, source_lang):
        return f"EN({source_lang}):{text}"


@pytest.fixture
def cfg():
    return Config()


@pytest.fixture
def pipe(cfg):
    return Pipeline(cfg, FakeSTT(), FakeTranslator())
