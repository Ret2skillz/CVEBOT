# CVEBOT
Discord Bot to fetch CVE

It fetches CVEs using NVD API.

It uses a predefined list of CWEs that are mainly associated with 'pwn' vulnerabilities.

It can fetches for last day, weej, month or trimester based on current day. Or it can fetches based on a given day range based on today or a provided date.

Command to start the bot is : watchmedo auto-restart --patterns="*.py" --recursive -- python main.py

allows to not have to restart bot on every update
