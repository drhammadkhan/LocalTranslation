import asyncio
from types import SimpleNamespace as NS

from vmt.channels.telegram_bot import TelegramChannel, is_allowed, pick_attachment
from vmt.queue import Job, Worker

from .conftest import FakeSTT, FakeTranslator, make_audio


def test_allowlist():
    assert is_allowed(1, {1}) and not is_allowed(2, {1}) and not is_allowed(None, {1})


def msg(**kw):
    base = dict(voice=None, audio=None, document=None)
    return NS(**{**base, **kw})


def test_pick_attachment():
    assert pick_attachment(msg(voice=NS(file_size=1)))[1] == ".ogg"
    doc = NS(file_name="PTT-2026.opus", mime_type="application/octet-stream")
    assert pick_attachment(msg(document=doc))[1] == ".opus"
    assert pick_attachment(msg(document=NS(file_name="x.pdf", mime_type="application/pdf"))) is None
    assert pick_attachment(msg()) is None


class FakeMsg:
    def __init__(self, **kw):
        self.__dict__.update(dict(voice=None, audio=None, document=None), **kw)
        self.sent = []

    async def reply_text(self, t):
        self.sent.append(t)
        return self

    async def edit_text(self, t):
        self.sent.append("EDIT:" + t)


class FakeBot:
    def __init__(self, src):
        self.src = src

    async def get_file(self, _id):
        src = self.src
        return NS(download_to_drive=lambda p: _copy(src, p))


async def _copy(src, dst):
    dst.write_bytes(src.read_bytes())


async def test_end_to_end_and_ignores_strangers(tmp_path, pipe):
    clip = make_audio(tmp_path / "v.ogg", [3])
    worker = Worker(pipe)
    task = asyncio.create_task(worker.run())
    ch = TelegramChannel("t", {42}, worker)

    stranger = FakeMsg(voice=NS(file_id="x", file_size=10))
    await ch.handle(NS(effective_message=stranger, effective_user=NS(id=7)), NS(bot=FakeBot(clip)))
    assert stranger.sent == []

    m = FakeMsg(voice=NS(file_id="x", file_size=10))
    await ch.handle(NS(effective_message=m, effective_user=NS(id=42)), NS(bot=FakeBot(clip)))
    await asyncio.wait_for(worker.queue.join(), 30)
    task.cancel()
    assert m.sent[0] == "⏳ Transcribing…"
    assert "🇬🇧 English" in m.sent[-1] and "bonjour" in m.sent[-1]


async def test_error_is_reported_and_audio_deleted(tmp_path, pipe):
    bad = tmp_path / "bad.ogg"
    bad.write_bytes(b"junk")
    errors = []
    worker = Worker(pipe)
    task = asyncio.create_task(worker.run())

    async def on_error(e):
        errors.append(str(e))

    await worker.submit(Job(bad, on_error=on_error))
    await asyncio.wait_for(worker.queue.join(), 30)
    task.cancel()
    assert errors and not bad.exists()
