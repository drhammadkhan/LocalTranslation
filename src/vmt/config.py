from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Channels(BaseModel):
    telegram: bool = True
    email: bool = False


class STTConfig(BaseModel):
    prefer: str = "whisper"
    whistle_languages: list[str] = ["en", "de", "fr", "es", "it", "nl", "pl"]
    whistle_binary: str = "models/needle"
    whistle_model: str = "models/whistle.cact"
    whisper_model: str = "medium"
    whisper_compute_type: str = "int8"
    whisper_threads: int = 4
    models_dir: str = "models"
    chunk_seconds: int = 28


class TranslateConfig(BaseModel):
    backend: str = "nllb"
    nllb_model_dir: str = "models/nllb-200-distilled-600M-ct2"
    nllb_tokenizer: str = "facebook/nllb-200-distilled-600M"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    summary: bool = False


class Limits(BaseModel):
    max_minutes: float = 10
    max_mb: float = 25


class Privacy(BaseModel):
    keep_audio: bool = False
    keep_text_days: int = 7


class Config(BaseModel):
    channels: Channels = Channels()
    stt: STTConfig = STTConfig()
    translate: TranslateConfig = TranslateConfig()
    limits: Limits = Limits()
    privacy: Privacy = Privacy()


class Secrets(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    telegram_bot_token: str = ""
    telegram_allowed_user_ids: str = ""
    email_imap_host: str = ""
    email_smtp_host: str = ""
    email_address: str = ""
    email_app_password: str = ""
    email_allowed_senders: str = ""

    @property
    def allowed_user_ids(self) -> set[int]:
        return {int(x) for x in self.telegram_allowed_user_ids.split(",") if x.strip()}

    @property
    def allowed_senders(self) -> set[str]:
        return {x.strip().lower() for x in self.email_allowed_senders.split(",") if x.strip()}


def load_config(path: str | Path = "config.yaml") -> Config:
    p = Path(path)
    if not p.exists():
        return Config()
    return Config.model_validate(yaml.safe_load(p.read_text()) or {})
