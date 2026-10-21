from __future__ import annotations

import re

from ..langs import nllb_code
from .base import Translator


class NLLBTranslator(Translator):
    """NLLB-200 distilled 600M via CTranslate2 (int8, CPU)."""

    def __init__(self, model_dir: str, tokenizer: str, threads: int = 4):
        self.model_dir, self.tokenizer_name, self.threads = model_dir, tokenizer, threads
        self._tr = self._tok = None

    def _load(self):
        if self._tr is None:
            import ctranslate2
            from transformers import AutoTokenizer

            self._tr = ctranslate2.Translator(self.model_dir, device="cpu",
                                              compute_type="int8", intra_threads=self.threads)
            self._tok = AutoTokenizer.from_pretrained(self.tokenizer_name)

    @staticmethod
    def split_sentences(text: str, max_chars: int = 400) -> list[str]:
        """NLLB degrades on long inputs, so translate sentence-sized pieces."""
        parts, cur = [], ""
        for s in re.split(r"(?<=[.!?…])\s+", text.strip()):
            if cur and len(cur) + len(s) > max_chars:
                parts.append(cur)
                cur = s
            else:
                cur = f"{cur} {s}".strip()
        if cur:
            parts.append(cur)
        return parts

    def translate(self, text: str, source_lang: str) -> str:
        self._load()
        self._tok.src_lang = nllb_code(source_lang)
        batch = [self._tok.convert_ids_to_tokens(self._tok.encode(p))
                 for p in self.split_sentences(text)]
        res = self._tr.translate_batch(batch, target_prefix=[["eng_Latn"]] * len(batch),
                                       beam_size=4)
        out = []
        for r in res:
            toks = r.hypotheses[0][1:]  # drop the target-language prefix token
            out.append(self._tok.decode(self._tok.convert_tokens_to_ids(toks)))
        return " ".join(out)
