from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .audio import AudioError
from .config import load_config
from .formatting import format_reply


def cli(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="vmt")
    ap.add_argument("-c", "--config", default="config.yaml")
    sub = ap.add_subparsers(dest="cmd", required=True)
    tr = sub.add_parser("transcribe", help="transcribe + translate one audio file")
    tr.add_argument("file", type=Path)
    tr.add_argument("--lang", help="force source language (ISO code)")
    tr.add_argument("--engine", choices=["whisper", "whistle"], help="force STT engine")
    tr.add_argument("--timings", action="store_true")
    sub.add_parser("doctor", help="check binaries, models, services and credentials")
    sub.add_parser("run", help="run the enabled channels (service mode)")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = load_config(args.config)
    if args.cmd == "transcribe":
        from .factory import build_pipeline
        try:
            res = build_pipeline(cfg).process(args.file, args.lang, args.engine)
        except AudioError as e:
            print(e, file=sys.stderr)
            return 2
        print(format_reply(res))
        if args.timings:
            print("\n" + ", ".join(f"{k}={v:.1f}s" for k, v in res.timings.items()))
    if args.cmd == "doctor":
        from .config import Secrets
        from .doctor import FAIL, render, run_checks
        checks = run_checks(cfg, Secrets())
        print(render(checks))
        return 1 if any(c.status == FAIL for c in checks) else 0
    if args.cmd == "run":
        import asyncio
        return asyncio.run(serve(cfg))
    return 0


async def serve(cfg) -> int:
    import asyncio

    from .channels.telegram_bot import TelegramChannel
    from .config import Secrets
    from .factory import build_pipeline
    from .queue import Worker

    secrets = Secrets()
    worker = Worker(build_pipeline(cfg), cfg.privacy.keep_audio)
    tasks = [asyncio.create_task(worker.run())]
    app = None
    if cfg.channels.telegram:
        if not secrets.telegram_bot_token or not secrets.allowed_user_ids:
            print("Telegram enabled but TELEGRAM_BOT_TOKEN / TELEGRAM_ALLOWED_USER_IDS unset", file=sys.stderr)
            return 1
        app = TelegramChannel(secrets.telegram_bot_token, secrets.allowed_user_ids, worker).build_app()
        await app.initialize()
        await app.start()
        await app.updater.start_polling()  # long polling: no inbound port needed
        logging.getLogger(__name__).info("telegram bot polling")
    try:
        await asyncio.gather(*tasks)
    finally:
        if app:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
