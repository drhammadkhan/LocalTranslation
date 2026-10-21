#!/usr/bin/env bash
# Run on the mini PC (needs internet access to huggingface.co). Idempotent.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v ffmpeg >/dev/null || { echo "Install ffmpeg: sudo apt install ffmpeg"; exit 1; }
command -v uv >/dev/null || { echo "Install uv: https://docs.astral.sh/uv/"; exit 1; }

uv sync --extra stt --extra nllb --extra telegram --extra email

WHISPER_MODEL="${WHISPER_MODEL:-medium}"   # tiny|base|small|medium|large-v3-turbo
echo "==> Downloading faster-whisper model: $WHISPER_MODEL"
uv run python - <<PY
from faster_whisper import download_model
print(download_model("$WHISPER_MODEL", cache_dir="models"))
PY

NLLB_DIR=models/nllb-200-distilled-600M-ct2
if [ ! -d "$NLLB_DIR" ]; then
  echo "==> Converting NLLB-200 distilled 600M to CTranslate2 int8 (one-off; pulls torch temporarily)"
  uvx --with torch --with transformers --with sentencepiece --from ctranslate2 \
    ct2-transformers-converter --model facebook/nllb-200-distilled-600M \
    --output_dir "$NLLB_DIR" --quantization int8
fi

echo "==> Optional: Ollama (only needed for translate.backend=ollama or summaries)"
echo "    curl -fsSL https://ollama.com/install.sh | sh && ollama pull qwen2.5:3b"
echo "==> Optional: Whistle - see docs/whistle-notes.md"
echo "Done. Try: uv run vmt transcribe some_voice_note.ogg --timings"
