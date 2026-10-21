from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import httpx

from .config import Config, Secrets

OK, WARN, FAIL = "ok", "warn", "FAIL"


@dataclass
class Check:
    status: str
    name: str
    detail: str = ""


def _whisper_model_present(cfg: Config) -> bool:
    m = cfg.stt.whisper_model
    if Path(m).is_dir():
        return True
    root = Path(cfg.stt.models_dir)
    return any(root.glob(f"**/models--*{m}*/snapshots/*/model.bin"))


def run_checks(cfg: Config, secrets: Secrets, http: httpx.Client | None = None) -> list[Check]:
    http = http or httpx.Client(timeout=10)
    out: list[Check] = []
    add = lambda s, n, d="": out.append(Check(s, n, d))

    for b in ("ffmpeg", "ffprobe"):
        add(OK if shutil.which(b) else FAIL, b, shutil.which(b) or "not on PATH")

    try:
        import faster_whisper  # noqa: F401
        add(OK, "faster-whisper installed")
    except ImportError:
        add(FAIL, "faster-whisper installed", "pip install '.[stt]'")
    if _whisper_model_present(cfg):
        add(OK, f"whisper model '{cfg.stt.whisper_model}'")
    else:
        add(FAIL, f"whisper model '{cfg.stt.whisper_model}'", "run scripts/setup_models.sh")

    t = cfg.translate
    if t.backend == "nllb":
        add(OK if Path(t.nllb_model_dir, "model.bin").exists() else FAIL,
            "NLLB model", t.nllb_model_dir)
    else:
        try:
            tags = http.get(f"{t.ollama_url}/api/tags").json()
            names = {m["name"] for m in tags.get("models", [])}
            have = t.ollama_model in names or f"{t.ollama_model}:latest" in names
            add(OK if have else FAIL, f"ollama model '{t.ollama_model}'",
                "" if have else f"ollama pull {t.ollama_model}")
        except Exception as e:
            add(FAIL, "ollama reachable", f"{t.ollama_url}: {type(e).__name__}")

    if cfg.stt.prefer == "whistle":
        ok = Path(cfg.stt.whistle_binary).exists() and Path(cfg.stt.whistle_model).exists()
        add(OK if ok else WARN, "whistle binary+model", "missing; falling back to whisper")

    if cfg.channels.telegram:
        if not secrets.telegram_bot_token:
            add(FAIL, "telegram token", "TELEGRAM_BOT_TOKEN unset")
        else:
            try:
                r = http.get(f"https://api.telegram.org/bot{secrets.telegram_bot_token}/getMe").json()
                add(OK if r.get("ok") else FAIL, "telegram token valid",
                    f"@{r['result']['username']}" if r.get("ok") else "rejected by Telegram")
            except Exception as e:
                add(FAIL, "telegram reachable", type(e).__name__)  # never echo the URL (has token)
        add(OK if secrets.allowed_user_ids else FAIL, "telegram allowlist",
            f"{len(secrets.allowed_user_ids)} user(s)" if secrets.allowed_user_ids
            else "TELEGRAM_ALLOWED_USER_IDS unset")
    return out


def render(checks: list[Check]) -> str:
    icon = {OK: "✓", WARN: "!", FAIL: "✗"}
    return "\n".join(f"{icon[c.status]} {c.name}" + (f" — {c.detail}" if c.detail else "")
                     for c in checks)
