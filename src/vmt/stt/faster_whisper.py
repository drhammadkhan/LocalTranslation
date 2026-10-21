from __future__ import annotations

import math
from pathlib import Path

from .base import STTEngine, Transcription


class FasterWhisperEngine(STTEngine):
    name = "whisper"

    def __init__(self, model: str, compute_type: str = "int8", threads: int = 4,
                 download_root: str | None = None):
        self._args = dict(model=model, compute_type=compute_type, threads=threads,
                          download_root=download_root)
        self._model = None

    def _load(self):
        if self._model is None:
            from faster_whisper import WhisperModel  # heavy import, load lazily

            a = self._args
            self._model = WhisperModel(a["model"], device="cpu", compute_type=a["compute_type"],
                                       cpu_threads=a["threads"], download_root=a["download_root"])
        return self._model

    def detect_language(self, wav: Path) -> str | None:
        from faster_whisper.audio import decode_audio

        audio = decode_audio(str(wav), sampling_rate=16000)[: 16000 * 30]
        lang, _prob, _all = self._load().detect_language(audio)
        return lang

    def transcribe(self, wav: Path, language: str | None = None) -> Transcription:
        segments, info = self._load().transcribe(
            str(wav), language=language, vad_filter=True, beam_size=5,
            condition_on_previous_text=False,
        )
        segs = list(segments)  # generator: decoding happens here
        text = " ".join(s.text.strip() for s in segs).strip()
        probs = [math.exp(s.avg_logprob) for s in segs]
        return Transcription(text, info.language, sum(probs) / len(probs) if probs else None)
