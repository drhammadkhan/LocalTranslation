from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from ..audio import AudioError
from ..formatting import format_reply, split_message
from ..queue import Job, Worker

log = logging.getLogger(__name__)

AUDIO_EXTS = {".opus", ".ogg", ".oga", ".m4a", ".mp3", ".wav", ".aac", ".amr", ".mp4", ".webm"}
TG_DOWNLOAD_LIMIT = 20 * 1024 * 1024  # Bot API getFile cap


def is_allowed(user_id: int | None, allowed: set[int]) -> bool:
    return user_id is not None and user_id in allowed


def pick_attachment(msg):
    """Return (file_object, suffix) for a voice/audio/audio-document message, else None."""
    if msg.voice:
        return msg.voice, ".ogg"
    if msg.audio:
        return msg.audio, Path(msg.audio.file_name or "a.mp3").suffix or ".mp3"
    d = msg.document
    if d:
        suffix = Path(d.file_name or "").suffix.lower()
        if (d.mime_type or "").startswith("audio/") or suffix in AUDIO_EXTS:
            return d, suffix or ".bin"
    return None


class TelegramChannel:
    def __init__(self, token: str, allowed_ids: set[int], worker: Worker):
        self.token, self.allowed, self.worker = token, allowed_ids, worker
        self.next_lang: dict[int, str] = {}  # per-user overrides, consumed by the next message
        self.next_engine: dict[int, str] = {}

    async def handle(self, update, context) -> None:
        msg, user = update.effective_message, update.effective_user
        if msg is None or not is_allowed(user.id if user else None, self.allowed):
            return  # unknown users get no response at all
        picked = pick_attachment(msg)
        if not picked:
            await msg.reply_text("Send or forward a voice note or audio file.")
            return
        att, suffix = picked
        if (att.file_size or 0) > TG_DOWNLOAD_LIMIT:
            await msg.reply_text("That file is over Telegram's 20 MB bot download limit.")
            return

        ahead = self.worker.ahead()
        status = await msg.reply_text(
            f"⏳ Queued ({ahead} ahead)…" if ahead else "⏳ Transcribing…")
        tmpdir = Path(tempfile.mkdtemp(prefix="vmt-tg-"))
        path = tmpdir / f"in{suffix}"
        await (await context.bot.get_file(att.file_id)).download_to_drive(path)

        async def on_start():
            if ahead:
                await status.edit_text("⏳ Transcribing…")

        async def on_done(res):
            parts = split_message(format_reply(res))
            await status.edit_text(parts[0])
            for p in parts[1:]:
                await msg.reply_text(p)

        async def on_error(e):
            text = str(e) if isinstance(e, AudioError) else "Sorry, something went wrong processing that."
            await status.edit_text(f"⚠️ {text}")

        await self.worker.submit(Job(
            path, self.next_lang.pop(user.id, None), self.next_engine.pop(user.id, None),
            on_start, on_done, on_error))

    def build_app(self):
        from telegram.ext import Application, MessageHandler, filters

        app = Application.builder().token(self.token).build()
        app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.handle))
        return app
