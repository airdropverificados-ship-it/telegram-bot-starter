# telegram-bot-starter

A minimal, dependency-light Telegram bot template in Python. Standard
library plus `requests` only — no frameworks, no build tools, no
magic. Clone it, add your token, and you have a working bot in
minutes.

## Features

- **Long polling** (`getUpdates`) and **webhook** modes
- Commands: `/start`, `/help`, `/echo <text>`, `/ping`
- A tiny **command registry** — adding a command is one function plus
  one line
- **SQLite** storage (stdlib `sqlite3`): stores users
  (`id`, `username`, `first_seen`) and a simple per-user message
  counter — nothing beyond what Telegram already sends
- Configuration **only from environment variables**
- The bot token is **never logged or printed**

## Polling vs webhook

| | Polling | Webhook |
| --- | --- | --- |
| How updates arrive | The bot asks Telegram repeatedly (`getUpdates`) | Telegram pushes updates to your server (`POST /webhook`) |
| Needs | Nothing — works behind NAT, on a laptop | A public HTTPS URL (e.g. behind a reverse proxy) |
| Best for | Development, small bots, personal projects | Production, higher traffic |

Start with polling. Switch to webhook when you deploy the bot on a
server with a public URL.

## Quickstart

```bash
git clone https://github.com/airdropverificados-ship-it/telegram-bot-starter.git
cd telegram-bot-starter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set BOT_TOKEN to the token from @BotFather
```

## Run

Polling mode (default):

```bash
python run.py --mode polling
```

Webhook mode (listens on `0.0.0.0:$WEBHOOK_PORT`, default `8080`):

```bash
python run.py --mode webhook
```

Then tell Telegram where to send updates (replace the placeholders):

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
  -d "url=https://your-domain.example/webhook" \
  -d "secret_token=<YOUR_WEBHOOK_SECRET>"
```

If `WEBHOOK_SECRET` is set, the server only accepts requests carrying
that exact value in the `X-Telegram-Bot-Api-Secret-Token` header
(wrong or missing secret → `401`). If it is unset, any request to
`/webhook` is accepted.

## How to add a command

Write a function in `starter/commands.py` and register it in
`COMMANDS`:

```python
def cmd_shout(ctx: Context) -> str:
    """Shout the text back in uppercase."""
    return ctx.args.upper() if ctx.args else "Usage: /shout <text>"

COMMANDS["shout"] = cmd_shout
```

That's it — `/shout hello` now replies `HELLO`. Handlers receive a
`Context` with `user_id`, `username`, `chat_id`, `args` (the text
after the command), and `conn` (the SQLite connection, or `None`).

## Project structure

```text
telegram-bot-starter/
├── run.py                 # Entry point: python run.py --mode polling|webhook
├── starter/
│   ├── __init__.py
│   ├── bot.py             # Telegram API client + polling loop
│   ├── commands.py        # Command registry and built-in commands
│   ├── config.py          # Environment-variable configuration
│   ├── storage.py         # SQLite users + counter
│   └── webhook.py         # stdlib http.server webhook (POST /webhook)
├── tests/                 # stdlib unittest, no network, no real token
├── .env.example           # Placeholder configuration
├── requirements.txt       # requests only
└── LICENSE                # MIT
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The tests run entirely offline with mocked HTTP and in-memory /
temporary databases — no real token needed.

## Configuration

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `BOT_TOKEN` | Yes | — | Bot token from [@BotFather](https://t.me/BotFather) |
| `WEBHOOK_SECRET` | No | — | Secret token verified on webhook requests |
| `WEBHOOK_PORT` | No | `8080` | Port the webhook server listens on |
| `DATABASE_PATH` | No | `bot.db` | SQLite database file |
| `POLLING_TIMEOUT` | No | `30` | Long-polling timeout in seconds |

## License

MIT — see [LICENSE](LICENSE).
