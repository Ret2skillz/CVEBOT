# CVEBOT
Discord Bot to fetch CVE

It fetches CVEs using NVD API.

It uses a predefined list of CWEs that are mainly associated with 'pwn' vulnerabilities.

It can fetches for last day, week, month or trimester based on current day. Or it can fetches based on a given day range based on today or a provided date.
it allows to filter based on severity of vulnerabilities (if cssv3 is provided).

Allow to save any cve base on its id and allow to add a group (for example if you want to group IOT vulns, Browser vulns, etc... to retrieve them more easily) to it and/or a tag.

can then search all your cve, or just by a tag or a group. The database uses sqlite3 for now.



Command to start the bot is : watchmedo auto-restart --patterns="*.py" --recursive -- python main.py

allows to not have to restart bot on every update

Note: the commands so far are not that intuitive or great, and the code is far from perfect, I may or may not update this later on and make it better 

TODO
1. Track CVEs other than low level ones like Web
2. Add some functionnalities for web3
3. Other features than CVEs (fetching reddit security communities, tracking interesting articles, etc)
4. Make it better i guess?
