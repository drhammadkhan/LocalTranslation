from __future__ import annotations

import httpx

from ..langs import language_name
from .base import Translator

TRANSLATE_PROMPT = (
    "Translate the following {lang} voicemail transcript into English. Translate faithfully. "
    "Keep names, numbers and phone numbers exactly as spoken. Do not summarise or add comments. "
    "Output only the translation.\n\n{text}"
)
SUMMARY_PROMPT = (
    "In 1-2 short lines summarise this voicemail: who called, what they want, and any callback "
    "number or time. Output only the summary.\n\n{text}"
)


class OllamaTranslator(Translator):
    def __init__(self, url: str, model: str, timeout: float = 600):
        self.url, self.model, self.timeout = url.rstrip("/"), model, timeout

    def _chat(self, prompt: str) -> str:
        r = httpx.post(f"{self.url}/api/chat", timeout=self.timeout, json={
            "model": self.model, "stream": False,
            "options": {"temperature": 0},
            "messages": [{"role": "user", "content": prompt}],
        })
        r.raise_for_status()
        return r.json()["message"]["content"].strip()

    def translate(self, text: str, source_lang: str) -> str:
        return self._chat(TRANSLATE_PROMPT.format(lang=language_name(source_lang), text=text))

    def summarise(self, english_text: str) -> str | None:
        return self._chat(SUMMARY_PROMPT.format(text=english_text))
