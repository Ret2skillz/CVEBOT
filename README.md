# CVEBOT

Discord bot to fetch CVE information and present paginated results in Discord using slash commands.

This repository provides a Discord bot that:
- Queries an NVD / vulnerability source via an nvd_api wrapper,
- Exposes slash commands to fetch CVEs (weekly/monthly/custom/id),
- Lets users save and manage CVEs (save/search/delete),
- Presents results as embeds with pagination.

This README explains how to set up, run, and troubleshoot the bot in a production-like way.

---

Table of contents
- Features
- Requirements
- Quick start (local development)
- Configuration (.env)
- Inviting the bot (permissions & scopes)
- Gateway intents & developer portal
- Running (development & production)
- Commands / Usage
- Pagination & permissions notes
- Troubleshooting (common errors)
- Contributing
- License
- Contact

---

Features
- Slash commands (app_commands) for quick CVE lookup:
  - Fetch by range: weekly, monthly, trimester, daily, custom
  - Fetch by ID
- Persistent user-saved CVEs with simple CRUD commands
- Paginated embed view with reaction-based controls
- Designed for both prefix-style commands and slash commands

Requirements
- Python 3.11+ (the bot was tested on Python 3.12)
- pip
- A Discord application + bot token (Developer Portal)
- Recommended: virtual environment to isolate dependencies
- (Optional) Database backend — the repo contains a `db` module. By default you can use an SQLite URL.

Quick start (local development)
1. Clone the repository
   git clone https://github.com/Ret2skillz/CVEBOT.git
   cd CVEBOT

2. Create and activate a virtual environment
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate

3. Install dependencies
   pip install -r requirements.txt

4. Create a .env file (see "Configuration" below)

5. Invite the bot to a test guild (see "Inviting the bot")

6. Run the bot
   # option A — development (auto-reload)
   watchmedo auto-restart --patterns="*.py" --recursive -- python main.py

   # option B — direct
   python main.py

Configuration (.env)
Create a `.env` file in the repo root with at least the following variables (example):

DISCORD_TOKEN="your_bot_token_here"
DATABASE_URL="sqlite:///data.db"         # or a Postgres/MySQL URL
CLIENT_ID="your_app_client_id"           # optional, used for invite links
GUILD_ID="your_test_guild_id"            # optional, used for local command sync
NVD_API_KEY=""                           # optional if your nvd_api wrapper requires an api key
LOG_LEVEL="INFO"

Notes:
- Keep tokens secret. Do not commit `.env` to git.
- If the bot uses other env vars (custom integrations), add them here.

Inviting the bot (permissions & scopes)
Use these OAuth scopes:
- bot
- applications.commands

Recommended permission sets (choose one):

- Full UX with reaction removal (recommended if you want the paginator to remove user reactions):
  - Permission integer: 355392
  - This includes MANAGE_MESSAGES so the bot can remove other users' reactions.

- Full UX without MANAGE_MESSAGES (safer):
  - Permission integer: 347200
  - The paginator will still work but will not be able to remove other users' reactions — it will attempt to remove its own reaction or ignore the failure.

Invite URL templates (replace CLIENT_ID):
- With MANAGE_MESSAGES:
  https://discord.com/oauth2/authorize?client_id=CLIENT_ID&permissions=355392&scope=bot%20applications.commands
- Without MANAGE_MESSAGES:
  https://discord.com/oauth2/authorize?client_id=CLIENT_ID&permissions=347200&scope=bot%20applications.commands

Gateway intents & Developer Portal settings
- In the Developer Portal > Bot:
  - Enable intents you need. For this project, ensure:
    - Server Members Intent — only if you need member lists (not required for most features)
    - Message Content Intent — only if you require raw message content (slash commands do not need this)
  - The bot requires standard intents to receive reaction events.
- In code (discord.py style):
```py
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
# enable only if you need them:
# intents.members = True
# intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
```

Important: make sure Developer Portal intents settings match the code.

Registering slash commands (guild vs global)
- For development: register commands for a single guild for instant updates.
- For production: you can register global commands, but expect up to ~1 hour of propagation.

Example (syncing guild commands):
```py
await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
```

Running (production)
- Recommended: run under systemd, Docker, or a process manager (pm2, supervisor).
- Ensure environment variables are set in the service manager.
- Rotate your token if it leaks. If you restart or change code, restart the process so the new code is used.

Commands / Usage
From the implemented cogs:

Fetch commands (fetch_vulns.py)
- /weekly [severity] — Fetch vulns of the last 7 days
- /monthly [severity] — Fetch vulns of the last 30 days
- /trimester [severity] — Fetch vulns of the last 120 days
- /daily [severity] — Fetch vulns of the last day
- /custom range [date?] [severity?] — Custom range (max 119)
- /id id — Fetch CVE by ID

Database commands (db_commands.py)
- /save cve_id [tag] [type_vuln] — Save CVE for your user
- /searchmy — List your saved CVEs
- /searchtag tag — Search saved CVEs by tag
- /searchtype type_vuln — Search saved CVEs by type
- /delete — Delete one of your saved CVEs (implementation dependent)

Pagination UX
- The bot uses reaction-based pagination:
  - Reactions: ⬅️ and ➡️ to move between pages.
  - The paginator attempts to remove the invoking user's reaction (requires MANAGE_MESSAGES).
  - If the bot lacks permission, it will attempt to remove its own reaction or ignore the error (non-fatal).
- Consider migrating to component-based pagination (buttons) for a smoother slash-command UX and to avoid MANAGE_MESSAGES.

Troubleshooting — common errors & fixes
- AttributeError: 'Interaction' object has no attribute 'send'
  - Fix: use `await interaction.response.send_message(...)` for the initial reply. If you previously deferred, use `await interaction.followup.send(...)`.

- NotFound: 404 Unknown interaction
  - The interaction was not acknowledged within 3 seconds. Fix: call `await interaction.response.defer()` early in long-running commands, then use followup for sending content.

- Forbidden: 403 Missing Permissions (when removing reactions)
  - The bot lacks MANAGE_MESSAGES. Either invite the bot with that permission, or update the paginator to not remove other users' reactions and catch the Forbidden exception.

- Slash commands not appearing or changes not propagating
  - Guild commands propagate instantly. Global commands can take up to ~1 hour to update. Use guild registration when developing.

- Bot not visible in Developer Portal
  - Ensure you’re logged into the correct Discord account. Run a small snippet in your running bot to print application info:
```py
app = await bot.application_info()
print(app.id, app.name, app.owner)
```

Security & best practices
- Keep tokens and API keys out of VCS. Use .env, secrets manager, or CI secret variables.
- Do not give the bot Administrator unless absolutely necessary.
- Rotate tokens if you suspect a leak.
- If you plan to run this in production and enable members/message_content intents, be mindful of Discord policy and privacy rules.

Development & contribution
- Use feature branches and open PRs for changes.
- Keep code style consistent. Run linters / formatters before opening a PR.
- Add unit tests for shared utilities where possible.

Example systemd unit (for reference)
[Unit]
Description=CVEBOT
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/CVEBOT
Environment="PATH=/path/to/CVEBOT/.venv/bin"
EnvironmentFile=/path/to/CVEBOT/.env
ExecStart=/path/to/CVEBOT/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

Switching to button-based paginator (recommendation)
- Buttons avoid MANAGE_MESSAGES and provide a better UX for slash commands.
- Consider migrating reaction paginator to discord.ui.Button based paginator when you have time.

Contributors
- Please open an issue for bugs or feature requests.
- When submitting PRs, include tests and explain the rationale.

License
- Add your chosen license here (e.g., MIT). If none, add one to `LICENSE` file.

Contact
- Author / maintainer: Ret2skillz (GitHub: Ret2skillz)
- For urgent support (e.g., stolen tokens), rotate the Discord token in the Developer Portal immediately.

---

If you want, I can:
- Create a ready-to-use invite URL with your CLIENT_ID plugged in.
- Add a systemd service file or Dockerfile + docker-compose manifest for easier deployments.
- Replace the reaction paginator with a button-based paginator and open a PR with working tests.
