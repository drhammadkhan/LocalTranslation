from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class Job:
    audio_path: Path
    lang: str | None = None
    engine: str | None = None
    # called with the finished (or failed) outcome; channel-specific
    on_start: Callable[[], Awaitable[None]] | None = None
    on_done: Callable[[object], Awaitable[None]] | None = None
    on_error: Callable[[Exception], Awaitable[None]] | None = None
    meta: dict = field(default_factory=dict)


class Worker:
    """Runs jobs one at a time so the mini PC's 4 cores aren't oversubscribed."""

    def __init__(self, pipeline, keep_audio: bool = False):
        self.pipeline, self.keep_audio = pipeline, keep_audio
        self.queue: asyncio.Queue[Job] = asyncio.Queue()
        self.busy = False

    def ahead(self) -> int:
        return self.queue.qsize() + (1 if self.busy else 0)

    async def submit(self, job: Job) -> int:
        n = self.ahead()
        await self.queue.put(job)
        return n

    async def run(self) -> None:
        while True:
            job = await self.queue.get()
            self.busy = True
            try:
                if job.on_start:
                    await job.on_start()
                res = await asyncio.to_thread(self.pipeline.process, job.audio_path,
                                              job.lang, job.engine)
                if job.on_done:
                    await job.on_done(res)
            except Exception as e:  # reported to the user; text never logged
                log.exception("job failed")
                if job.on_error:
                    try:
                        await job.on_error(e)
                    except Exception:
                        log.exception("error handler failed")
            finally:
                self.busy = False
                if not self.keep_audio:
                    job.audio_path.unlink(missing_ok=True)
                self.queue.task_done()
