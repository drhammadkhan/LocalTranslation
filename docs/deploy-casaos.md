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
