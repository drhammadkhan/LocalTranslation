from __future__ import annotations

from abc import ABC, abstractmethod


class Translator(ABC):
    @abstractmethod
    def translate(self, text: str, source_lang: str) -> str: ...

    def summarise(self, english_text: str) -> str | None:
        return None
