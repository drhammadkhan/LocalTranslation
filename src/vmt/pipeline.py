from __future__ import annotations

import logging
import tempfile
import time
from pathlib import Path

from . import audio
from .config import Config
from .formatting import Result
from .langs import language_name
from .stt.base import STTEngine, Transcription
from .translate.base import Translator

log = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, cfg: Config, whisper: STTEngine, translator: Translator | None,
                 whistle: STTEngine | None = None):
        self.cfg, self.whisper, self.translator, self.whistle = cfg, whisper, translator, whistle

    # -- engine selection -------------------------------------------------
    def _pick(self, lang: str | None, force: str | None) -> STTEngine:
        if force == "whisper" or self.whistle is None:
            return self.whisper
        if force == "whistle":
            return self.whistle
        if self.cfg.stt.prefer == "whistle" and lang in self.cfg.stt.whistle_languages:
            return self.whistle
        return self.whisper

    @staticmethod
    def looks_bad(t: Transcription, dur: float) -> bool:
        words = len(t.text.split())
        return words == 0 or (dur > 10 and words < dur / 6)  # <1 word per 6 s is suspicious

    def _run_engine(self, eng: STTEngine, wav: Path, tmp: Path, dur: float,
                    lang: str | None) -> Transcription:
        if eng.max_window_s is None or dur <= eng.max_window_s:
            return eng.transcribe(wav, lang)
        size = self.cfg.stt.chunk_seconds
        windows = audio.plan_chunks(dur, audio.find_silences(wav), size)
        parts, detected = [], lang
        for i, (a, b) in enumerate(windows):
            t = eng.transcribe(audio.cut(wav, a, b, tmp / f"chunk{i}.wav"), lang)
            parts.append(t.text)
            detected = detected or t.language
        return Transcription(audio.join_transcripts(parts), detected)

    # -- main entry -------------------------------------------------------
    def process(self, path: Path, lang: str | None = None, engine: str | None = None) -> Result:
        lim, timings = self.cfg.limits, {}
        audio.check_limits(path, lim.max_minutes, lim.max_mb)
        with tempfile.TemporaryDirectory(prefix="vmt-") as td:
            tmp = Path(td)
            t0 = time.monotonic()
            wav = audio.to_wav(path, tmp / "in.wav")
            dur = audio.duration(wav)
            timings["convert"] = time.monotonic() - t0

            t0 = time.monotonic()
            lang = lang or self.whisper.detect_language(wav)
            timings["langid"] = time.monotonic() - t0

            t0 = time.monotonic()
            eng = self._pick(lang, engine)
            t = self._run_engine(eng, wav, tmp, dur, lang)
            if eng is not self.whisper and engine is None and self.looks_bad(t, dur):
                log.warning("%s output looked bad; retrying with %s", eng.name, self.whisper.name)
                eng = self.whisper
                t = self._run_engine(eng, wav, tmp, dur, lang)
            timings["stt"] = time.monotonic() - t0
            lang = lang or t.language or "und"

        translation = summary = None
        if lang != "en" and t.text and self.translator:
            t0 = time.monotonic()
            translation = self.translator.translate(t.text, lang)
            timings["translate"] = time.monotonic() - t0
        if self.cfg.translate.summary and self.translator and t.text:
            t0 = time.monotonic()
            summary = self.translator.summarise(translation or t.text)
            timings["summary"] = time.monotonic() - t0
        log.info("processed %.0fs audio with %s in %s", dur, eng.name,
                 {k: round(v, 1) for k, v in timings.items()})  # timings only, never text
        return Result(lang, language_name(lang), eng.name, dur, t.text, translation, summary, timings)
