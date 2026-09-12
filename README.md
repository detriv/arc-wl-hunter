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

# X (Twitter) Session Cookies
# Get from Chrome: F12 → Application → Cookies → x.com → auth_token & ct0
X_AUTH_TOKEN=
X_CT0=

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

X login via browser automation is often blocked. Instead, we use session cookies from your existing browser.

```bash
python app.py --login
```

This will show instructions. Here's the summary:

1. Open https://x.com in Chrome/Firefox and login normally
2. Press `F12` → **Application** → **Cookies** → `https://x.com`
3. Find `auth_token` → copy the **Value**
4. Find `ct0` → copy the **Value**
5. Open `.env` and paste:

```env
X_AUTH_TOKEN=<paste auth_token value here>
X_CT0=<paste ct0 value here>
```

6. Test:

```bash
python app.py --test-x
```

> **Note:** Session cookies typically last weeks/months. If auth fails, refresh them from your browser.

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
- NEVER share your X session cookies (`auth_token`, `ct0`)
- NEVER expose your Telegram token
- If cookies are compromised, change your X password immediately
- Use a dedicated X account

---

## Troubleshooting

### X session expired / not authenticated

Your cookies may be expired. Refresh them:

1. Open https://x.com in Chrome/F2
2. F12 → Application → Cookies → https://x.com
3. Copy fresh `auth_token` and `ct0` values
4. Update `.env`

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

## Docker Deployment

### Build and run locally

```bash
docker compose up -d --build
```

### View logs

```bash
docker compose logs -f arc-wl-hunter
```

### Stop

```bash
docker compose down
```

### Deploy to cloud (fastapicloud, Railway, etc)

1. Push to GitHub
2. Connect repo to your cloud platform
3. Set environment variables in platform dashboard:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `X_AUTH_TOKEN`
   - `X_CT0`
   - `DISCORD_WEBHOOK_URL` (optional)
4. Set start command: `python app.py --web`

### Health check endpoint

```
GET /health
```

Returns:
```json
{
  "status": "healthy",
  "telegram": true,
  "discord": true,
  "x_cookies": true,
  "bot_running": true
}
```

### Stats endpoint

```
GET /stats
```

Returns database statistics.

---

## License

MIT
