from __future__ import annotations

from .config import Config
from .pipeline import Pipeline
from .stt.faster_whisper import FasterWhisperEngine
from .stt.whistle import WhistleEngine
from .translate.base import Translator


def build_translator(cfg: Config) -> Translator:
    t = cfg.translate
    if t.backend == "ollama":
        from .translate.ollama import OllamaTranslator
        return OllamaTranslator(t.ollama_url, t.ollama_model)
    from .translate.nllb import NLLBTranslator
    return NLLBTranslator(t.nllb_model_dir, t.nllb_tokenizer, cfg.stt.whisper_threads)


def build_pipeline(cfg: Config) -> Pipeline:
    s = cfg.stt
    whisper = FasterWhisperEngine(s.whisper_model, s.whisper_compute_type, s.whisper_threads,
                                  download_root=s.models_dir)
    whistle = WhistleEngine(s.whistle_binary, s.whistle_model)
    return Pipeline(cfg, whisper, build_translator(cfg), whistle if whistle.available() else None)
