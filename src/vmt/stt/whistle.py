"""Cactus Whistle via subprocess.

UNVERIFIED: the CLI flags and output format below follow the README's description
(`needle --model whistle.cact --audio clip.wav`). Confirm against `needle --help`
on the target machine and record the findings in docs/whistle-notes.md.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .base import STTEngine, Transcription


class WhistleEngine(STTEngine):
    name = "whistle"
    max_window_s = 30.0

    def __init__(self, binary: str, model: str, timeout: float = 120):
        self.binary, self.model, self.timeout = binary, model, timeout

    def available(self) -> bool:
        return Path(self.binary).exists() and Path(self.model).exists()

    def transcribe(self, wav: Path, language: str | None = None) -> Transcription:
        cmd = [self.binary, "--model", self.model, "--audio", str(wav)]
        if language:
            cmd += ["--language", language]  # TODO verify flag name
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
        if r.returncode != 0:
            raise RuntimeError(f"whistle failed: {r.stderr.strip()[:200]}")
        return self.parse(r.stdout)

    @staticmethod
    def parse(out: str) -> Transcription:
        out = out.strip()
        try:  # JSON output, if the binary emits it
            d = json.loads(out)
            return Transcription(d.get("text") or d.get("response") or "",
                                 d.get("language"), d.get("confidence"))
        except json.JSONDecodeError:
            return Transcription(out)  # plain text fallback
