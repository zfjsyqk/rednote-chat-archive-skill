# RedNote Chat Archive Skill

[中文](README.md) | [English](README.en.md)

A Codex maintenance skill and companion local web application for archiving Xiaohongshu (RedNote) conversations on your Mac. Real chat archives and optional AI conversations use separate SQLite databases. The website listens only on `127.0.0.1:8765`.

**Only records already available in the Mac client's local database can be backed up. This does not guarantee complete server history.** No private messages, credentials, avatars, screenshots, or third-party sticker assets are distributed.

## Features

- Add a conversation using a public account number, internal user ID, full profile URL, or profile short-link/share text. Identity resolution uses explicit fields and validated profile redirects, never nickname guessing.
- Create a consistent, read-only SQLite source snapshot; preserve raw metadata and normalized messages; download available media incrementally.
- View text, images, stickers, audio, video, calls, system notices, recalled-message notices, and shared-note cards. Audio/video conversion requires ffmpeg.
- Chronological messages with the latest visible on opening; load earlier batches of 200 while scrolling upward and preserve the scroll anchor.
- Search, date filters, and timeline navigation to the first actual message on the selected day. Missing dates report the day actually reached.
- Blue outgoing bubbles, gray incoming bubbles, circular avatars, 14px text/input, 100px standalone stickers, and copy/save actions beside messages.
- Message times use Asia/Shanghai: today `HH:mm:ss`, other days in the current Monday-based week `weekday HH:mm:ss`, older dates `YYYY-MM-DD HH:mm:ss`.
- Conversation menu: **Update backup**, **Export backup**, **Delete AI records**, **Delete backup**. The Chinese interface uses uniform outline icons, content-sized rounded menus, gray item hover states, and red destructive backup actions.
- Import UTF-8 JSON/CSV and export one conversation's real text records as JSON. Export currently filters the full API result in the frontend; it does not bundle media or AI messages.
- Save media using the browser's save picker, or an absolute local destination; existing files are not overwritten.

## Requirements and startup

Python 3.10+ with its standard library. No third-party Python packages are required. Install ffmpeg/ffprobe for media conversion. Mac database extraction requires a supported RedNote client schema, an existing local database, and appropriate macOS file access. JSON/CSV viewing does not require the client.

```sh
git clone https://github.com/zfjsyqk/rednote-chat-archive-skill.git
cd rednote-chat-archive-skill
python3 app.py
```

Open [the local viewer](http://127.0.0.1:8765/). Stop with Ctrl+C. Refresh after frontend changes; restart after Python changes. Restarting invalidates login sessions but preserves the password and records.

The release attempts to locate a single matching database under `~/Library/Containers`. If none or several exist, explicitly configure it before starting:

```sh
export REDNOTE_SOURCE_DB="/path/to/PrivateMessage.db"
python3 app.py
```

Open the contact's profile and conversation in the Mac client and load the history you need. Then use **添加会话** (Add conversation) in the viewer. Check the actual exported time range and attachment failure count. Public account numbers and 24-character internal IDs differ; profile links can resolve missing mappings. The parser reads the first short-link redirect and validates the destination domain/profile path instead of following into a login page.

Command-line exports always require an explicit target:

```sh
python3 export_rednote.py --user '<account number or profile URL>'
python3 media.py
```

## Optional AI conversations

In **系统设置** (System settings), select OpenAI API or DeepSeek API, enter an API key and model name, and save. Provider credentials and models are independent. Defaults are `gpt-4.1-mini` and `deepseek-flash`; model names are editable and availability depends on the provider/account.

Only the selected conversation's relevant historical text samples and recent AI context are sent to the selected provider when you send a message. Examples use the other person's actual words; your historical messages provide context. This is approximate style simulation, not model training or a representation of that person's current feelings. The application never sends messages to RedNote.

AI replies show `Name-AI`. Your message appears immediately with an avatar and “replying…” placeholder; successful replies replace the placeholder. Failed requests show an error and restore the draft; only successful message pairs are persisted. Requests have bounded timeouts and explicit credential/quota/network errors.

AI messages are stored in a separate database and excluded from real exports, searches, and timelines. Default retention is 1 day; alternatives are 7, 30, 60 days, or permanent. Cleanup runs every 30 seconds while the service runs, on reads, and at startup. Closed services do not delete on a timer; expired records are cleared on reopening. Changing retention recalculates expiry from each message's creation time. Deletion prevents late replies from resurrecting removed records.

Keys remain server-side in `data/ai_config.json` with 0600 permissions; saved keys are not returned to the browser. Leaving the key input empty preserves it. `OPENAI_API_KEY` and `DEEPSEEK_API_KEY` environment variables are also supported. ChatGPT Plus does not include ordinary API usage credit. OpenAI requests use `store:false`, which does not imply zero provider-side retention.

## Passwords and deletion

No password means direct local access. Setting a password protects both APIs and media, with salted scrypt hashes, 8-hour sessions, and login attempt limits. You can change/remove the password or lock immediately. **The password does not encrypt files on disk.** Do not expose this service publicly.

**Delete backup** requires a second confirmation using the current access password. Set a password first if none exists. It removes the selected conversation's real messages, raw metadata, AI records, registration, project exports, exclusive attachments, and matching identity rows from project source snapshots. Shared media and other conversations are retained. Deletion is blocked during active backup jobs and cannot be undone through the app. It does not alter the client's original database or files previously saved outside the project. Adding the contact again may restore records still present in the client.

## Import format

JSON accepts an array or an object with a `messages` array:

```json
[{"contact":"Example contact","sender":"我","time":"2026-10-12 10:00:00","content":"Fictional example"}]
```

CSV headers: `contact,sender,time,content`. Use UTF-8 and sortable `YYYY-MM-DD HH:mm:ss` timestamps (milliseconds optional). `sender=我` means outgoing. Imports are limited to 20MB; split larger files. Ordinary imports lack native metadata, so they cannot infer media or specialized message types.

## Local files

| Path | Contents |
| --- | --- |
| `data/chats.sqlite3` | Real messages, raw metadata, contacts, media index |
| `data/source-backups/` | Consistent full-client snapshots, potentially multiple contacts |
| `data/exports/` | Per-contact normalized/raw JSON and range reports |
| `data/media/` | Original and converted media |
| `data/profiles.json` | Avatar/sticker mappings |
| `data/security.json` | Password salt/hash |
| `data/ai_chats.sqlite3` | AI messages, retention, deletion generations |
| `data/ai_config.json` | Provider configuration and secrets |

The entire `data/` directory is ignored by Git. For a complete local backup, preserve databases, media, exports, and mappings with the service stopped or using SQLite backup APIs. Full-client snapshots must not be shared as single-contact exports.

## Install the skill

Copy `skills/rednote-chat-archive/` into `~/.codex/skills/rednote-chat-archive/` and ask Codex to use `$rednote-chat-archive` to maintain this checkout. The skill documents constraints and workflows; installing it does not start the website or supply private records. Chinese and English reference documentation is included.

## Development and checks

```sh
python3 test_contacts.py
python3 test_backup_delete.py
python3 test_ai_chat.py
python3 test_providers.py
python3 test_app.py
node --check static/app.js
```

Tests use temporary databases, synthetic schemas, and mock model calls. HTTP tests bind a temporary loopback port. Node is only needed for optional JavaScript syntax checks.

Every feature, interaction, configuration, or style change must update both READMEs, the skill, and affected reference documents in the same task. Keep real/AI databases separate and never modify the source client database.

## Limits and distribution

Client schemas can change; iPhone/Android/Windows extraction, deleted-message recovery, complete official sticker resources, and automatic RedNote sending are not implemented. Some native animations are not reproduced. Media completion must be checked against failure counts; expired links may remain unavailable. Profile mappings do not have full multi-process update protection.

The public package removes fixed personal paths and seeded account identities. It contains source and documentation only; no third-party media assets are included. No open-source license has been selected, so public visibility alone does not grant a general redistribution license.
