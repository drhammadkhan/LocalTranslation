# Deploying on CasaOS (Debian mini PC)

1. `git clone` this repo onto the mini PC, `cd` into it.
2. `cp .env.example .env` and fill in `TELEGRAM_BOT_TOKEN` (from @BotFather) and
   `TELEGRAM_ALLOWED_USER_IDS` (your numeric ID, e.g. from @userinfobot).
3. Download models once, on the host: `./scripts/setup_models.sh`
   (puts the whisper model and converted NLLB in `./models`, mounted into the container).
4. `docker compose up -d --build`. In CasaOS you can instead use
   App Store -> Custom Install -> Import and paste `docker-compose.yml`.
5. `docker logs -f vmt` should show "telegram bot polling". Forward a voice note to the bot.

No ports are published; the bot uses Telegram long-polling (outbound only).
Logs contain timings and errors only, never transcript text.

## Health check
`docker exec vmt vmt doctor` checks ffmpeg, the whisper/NLLB models, Ollama (if used) and that
the Telegram token is valid. It exits non-zero on any failure and never prints the token.

## Surviving reboots / crashes
`restart: unless-stopped` restarts the container after a crash and after a reboot, as long as
Docker itself starts at boot (`sudo systemctl enable docker`, the default on Debian).
Logs rotate at 3 x 5 MB: `docker logs -f vmt`.

No Docker? `deploy/vmt.service` is a systemd unit that does the same job natively.
