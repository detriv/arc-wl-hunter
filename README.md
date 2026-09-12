# Arc NFT Whitelist Hunter

Arc NFT Whitelist Hunter monitors X (Twitter) for NFT whitelist opportunities related to Arc Network, analyzes them, stores results in SQLite, and sends alerts to Telegram.

---

## Requirements

- Python 3.11+
- Chromium (installed via Playwright)
- X (Twitter) account
- Telegram bot (for notifications)

---

## Installation

```bash
git clone <repository>
cd arc-wl-hunter

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install chromium
```

---

## Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Telegram (required for notifications)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Browser
BROWSER_PROFILE_DIR=data/browser-profile
BROWSER_HEADLESS=false

# Monitoring
POLL_INTERVAL_SECONDS=300

# Search behavior
SEARCH_DELAY_SECONDS=2
SCROLL_DELAY_SECONDS=2
MAX_POSTS_PER_QUERY=50
MAX_SCROLLS_PER_QUERY=10

# Scoring thresholds
MIN_SCORE=60
HIGH_PRIORITY_SCORE=80

# Logging
LOG_LEVEL=INFO
```

---

## Telegram Bot Setup

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the bot token
4. Start a chat with your bot (send `/start`)
5. Get your Chat ID by messaging [@userinfobot](https://t.me/userinfobot) or visiting:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
6. Put both values in `.env`

Test:

```bash
python app.py --test-telegram
```

---

## X Account Setup

```bash
python app.py --login
```

1. Chromium opens
2. Log into your X account manually
3. Return to terminal and press ENTER
4. Session is saved to `data/browser-profile/`

---

## Usage

### Run continuously

```bash
python app.py
```

### One scan

```bash
python app.py --once
```

### Test X extraction

```bash
python app.py --test-x
```

### Test Telegram

```bash
python app.py --test-telegram
```

### Database statistics

```bash
python app.py --stats
```

### Login to X

```bash
python app.py --login
```

---

## Architecture

```
                 ┌───────────────┐
                 │      X        │
                 └───────┬───────┘
                         │
                  Playwright
                         │
                         ▼
                 ┌───────────────┐
                 │ X Provider    │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │ Post Parser   │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │ Scoring       │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │ SQLite        │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │ Telegram      │
                 └───────────────┘
```

---

## Security

- NEVER commit `.env`
- NEVER share your browser profile
- NEVER expose your Telegram token
- The browser profile contains sensitive session data
- Use a dedicated X account

---

## Troubleshooting

### X session expired

```bash
python app.py --login
```

### Chromium does not launch

```bash
playwright install chromium
```

### Telegram test failed

- Verify `TELEGRAM_BOT_TOKEN` is correct
- Verify `TELEGRAM_CHAT_ID` is correct
- Make sure you started a chat with the bot

### No X posts found

- Check your internet connection
- Verify X session is valid with `--login`
- X may have changed its UI (selectors need updating)

---

## License

MIT
