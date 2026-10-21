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
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
