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
- Inviting the bot — exact scopes & permissions
- Gateway intents & Developer Portal settings
- Hosting online (always-on + automatic updates) — see [HOSTING.md](HOSTING.md)
  - OVH VPS
  - Hetzner Cloud
  - DigitalOcean Droplet
  - AWS EC2 Free Tier
  - Railway (free PaaS)
  - Render (free PaaS)
- Automatic updates via GitHub Actions
- Commands / Usage
- Pagination & permissions notes
- Troubleshooting (common errors)
- Security & best practices
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
- (Optional) Database backend — the repo contains a `db` module. By default it uses SQLite.

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
   # option A — development (auto-reload on file save)
   watchmedo auto-restart --patterns="*.py" --recursive -- python main.py

   # option B — direct
   python main.py

Configuration (.env)
Copy `.env.example` to `.env` and fill in your values:

   cp .env.example .env

Minimum required variables:

   DISCORD_TOKEN="your_bot_token_here"
   NVD_API_KEY=""              # optional but strongly recommended
   GITHUB_TOKEN=""             # optional, used for PoC lookups
   LOG_LEVEL="INFO"            # DEBUG | INFO | WARNING | ERROR

Notes:
- Keep tokens secret. Never commit `.env` to git (it is already in `.gitignore`).

---

Inviting the bot — exact scopes & permissions
Step-by-step in the Developer Portal (https://discord.com/developers/applications):

1. Open your application → OAuth2 → URL Generator.

2. Under SCOPES tick exactly:
   [x] bot
   [x] applications.commands        <- required for / slash commands to register & appear

3. Under BOT PERMISSIONS tick:

   Permission            | Why it is needed
   ----------------------|--------------------------------------------------
   View Channels         | Bot must be able to see the channel it replies in
   Send Messages         | Post CVE embeds
   Send Messages in Threads | (optional) if you use threads
   Embed Links           | CVE results are sent as rich embeds
   Attach Files          | CSV export feature
   Read Message History  | Required for reaction-based paginator
   Add Reactions         | Bot adds ⬅️ ➡️ reactions for page navigation
   Manage Messages       | Bot removes old reactions during pagination (optional but recommended)

   Permission integer (with Manage Messages):    355392
   Permission integer (without Manage Messages): 347200

4. Copy the generated URL at the bottom and open it in your browser to add the
   bot to your server.

Invite URL templates (replace CLIENT_ID with your application's client ID):

   With Manage Messages (recommended):
   https://discord.com/oauth2/authorize?client_id=CLIENT_ID&permissions=355392&scope=bot%20applications.commands

   Without Manage Messages (safer / stricter):
   https://discord.com/oauth2/authorize?client_id=CLIENT_ID&permissions=347200&scope=bot%20applications.commands

Why applications.commands is mandatory for slash commands
- Without it the bot cannot register / commands with Discord.
- Even if the Python code registers commands, users will not see them in the
  UI unless this scope is present in the invite.

---

Gateway intents & Developer Portal settings
In Developer Portal -> your application -> Bot page:

1. Scroll to "Privileged Gateway Intents".
2. Enable:
   [x] Message Content Intent  (required — main.py sets intents.message_content = True)
3. Leave the following OFF unless you need them:
   [ ] Server Members Intent
   [ ] Presence Intent

In code (already set in main.py):
```py
intents = discord.Intents.default()
intents.message_content = True   # must match the Developer Portal toggle
```

Important: the Developer Portal toggle and the code must agree.
If the toggle is OFF but the code requests it (or vice-versa), you will get an
error or silently lose events.

---

Hosting online — always-on + automatic updates

For full step-by-step provider-specific instructions see **[HOSTING.md](HOSTING.md)**.

Providers covered: OVH VPS · Hetzner Cloud · DigitalOcean · AWS EC2 Free Tier
· Railway (free PaaS) · Render (free PaaS).

Quick summary — on any Linux VPS (after installing Docker):

   git clone https://github.com/Ret2skillz/CVEBOT.git ~/cvebot
   cd ~/cvebot
   cp .env.example .env && nano .env   # set DISCORD_TOKEN etc.
   docker compose up -d               # starts bot + Watchtower (auto-updates)
   docker compose logs -f cvebot      # verify login

Watchtower polls GitHub Container Registry every 5 minutes. When GitHub Actions
pushes a new :latest image (on every merge to main), Watchtower pulls it and
restarts the container — no manual SSH needed.

For bare-metal / no-Docker setups, see the systemd section in HOSTING.md.

---

Automatic updates via GitHub Actions
The repository includes `.github/workflows/docker-publish.yml`.

What it does:
- Triggers on every push to main (and as a dry-run build on PRs).
- Builds the Docker image.
- Pushes it to GitHub Container Registry (ghcr.io) as:
    ghcr.io/YOUR_GITHUB_USERNAME/cvebot:latest
    ghcr.io/YOUR_GITHUB_USERNAME/cvebot:sha-<short-sha>

Combined with Watchtower on your server, the full flow is:
  1. You push a commit to main (or merge a PR).
  2. GitHub Actions builds and pushes a new :latest image to GHCR (~2 min).
  3. Watchtower notices the new image within 5 minutes and restarts the bot
     container with the new code.

No manual SSH or deployment steps required.

---

Registering slash commands (guild vs global)
- For development: register commands for a single guild for instant updates:
```py
await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
```
- For production: global sync (already in main.py via `await self.tree.sync()`).
  Expect up to ~1 hour for Discord to propagate global commands after first run
  or after adding new commands.

---

Commands / Usage
From the implemented cogs:

Fetch commands (fetch_vulns.py)
- /weekly [severity] [product] [as_csv] [exact] — Fetch vulns of the last 7 days
- /monthly [severity] [product] [as_csv] [exact] — Fetch vulns of the last 30 days
- /trimester [severity] [product] [as_csv] [exact] — Fetch vulns of the last 120 days
- /daily [severity] [product] [as_csv] [exact] — Fetch vulns of the last day
- /custom range [date] [severity] [product] [as_csv] [exact] — Custom range (max 119 days)
- /id id [product] [as_csv] [exact] — Fetch CVE by ID

Database commands (db_commands.py)
- /save cve_id [tag] [type_vuln] — Save CVE for your user
- /searchmy — List your saved CVEs
- /searchtag tag — Search saved CVEs by tag
- /searchtype type_vuln — Search saved CVEs by type
- /delete — Delete one of your saved CVEs

Pagination UX
- The bot uses reaction-based pagination:
  - Reactions: ⬅️ and ➡️ to move between pages.
  - The paginator attempts to remove the invoking user's reaction (requires Manage Messages).
  - If the bot lacks permission, it will attempt to remove its own reaction or ignore the error (non-fatal).
- Consider migrating to component-based pagination (buttons) for a smoother slash-command UX
  and to avoid needing Manage Messages.

---

Troubleshooting — common errors & fixes
- AttributeError: 'Interaction' object has no attribute 'send'
  - Fix: use `await interaction.response.send_message(...)` for the initial reply.
    If you previously deferred, use `await interaction.followup.send(...)`.

- NotFound: 404 Unknown interaction
  - The interaction was not acknowledged within 3 seconds.
    Fix: call `await interaction.response.defer()` early in long-running commands,
    then use followup for sending content.

- Forbidden: 403 Missing Permissions (when removing reactions)
  - The bot lacks Manage Messages. Either invite the bot with that permission,
    or update the paginator to not remove other users' reactions and catch the
    Forbidden exception.

- Slash commands not appearing or changes not propagating
  - Guild commands propagate instantly.
    Global commands can take up to ~1 hour to update.
    Use guild registration when developing.

- Bot not visible in Developer Portal
  - Ensure you're logged into the correct Discord account.
    Run a small snippet in your running bot to print application info:
```py
app = await bot.application_info()
print(app.id, app.name, app.owner)
```

---

Security & best practices
- Keep tokens and API keys out of VCS. Use .env, secrets manager, or CI secret variables.
- Do not give the bot Administrator unless absolutely necessary.
- Rotate tokens if you suspect a leak.
- If you plan to run this in production and enable members/message_content intents,
  be mindful of Discord policy and privacy rules.

Development & contribution
- Use feature branches and open PRs for changes.
- Keep code style consistent. Run linters / formatters before opening a PR.
- Add unit tests for shared utilities where possible.

---

Contributors
- Please open an issue for bugs or feature requests.
- When submitting PRs, include tests and explain the rationale.

License
- MIT — see the `LICENSE` file.

Contact
- Author / maintainer: Ret2skillz (GitHub: Ret2skillz)
- For urgent support (e.g., stolen tokens), rotate the Discord token in the Developer Portal immediately.
