# Cactus Whistle notes

Status: **unverified, optional.** Whistle is not required for the pipeline to work;
the default engine is faster-whisper, and `stt.prefer: whisper` never touches Whistle.

## What is confirmed (from public coverage, 2026-10-21)
- Released 2 Oct 2026 by Cactus Compute, Apache 2.0, ~16.9 MB, CPU only.
- 7 languages: en, de, fr, es, it, nl, pl. 30 s max window. Auto language detect.
- Vendor benchmarks only; reviewers report weaker results on natural conversational speech.

## Not confirmed (could not verify from the dev container)
- A Linux x86_64 build of the `needle` binary. The main `cactus-compute/cactus` repo lists
  no release assets and no mention of Whistle; it documents `cactus transcribe --file --language`
  and says it builds on Debian/Ubuntu, so a source build on the mini PC may be the route.
- The exact CLI flags and output format.

## To do on the mini PC
1. Find the official Whistle model card / repo, download `whistle.cact`.
2. Get or build the binary, run `--help`, and paste the real flags and a sample output here.
3. Adjust `src/vmt/stt/whistle.py` (`transcribe`, `parse`) to match, set `stt.whistle_binary`,
   `stt.whistle_model` in config.yaml, then compare with `vmt transcribe --engine whistle|whisper`.

Also check the 6th-gen CPU is fast enough to need Whistle at all: whisper `small`/`medium`
int8 may already be fine given the "a few minutes is OK" latency budget.
