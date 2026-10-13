# RedNote Chat Archive maintenance guide

Maintain the companion local Python/SQLite and native HTML/CSS/JS application. This guide complements the canonical SKILL.md.

Read selectively: [Product](references/product.en.md), [Architecture](references/architecture.en.md), [AI](references/ai.en.md), [Operations](references/operations.en.md).

Keep the original client database read-only and use SQLite backup APIs. Real records use data/chats.sqlite3; AI uses data/ai_chats.sqlite3. Never merge AI into real exports or send messages through RedNote. Bind only to loopback; password checks protect backend APIs and media, not merely DOM visibility. Passwords do not encrypt disk files.

Identity requires explicit fields/cache mappings or validated profile URLs, never nickname guessing. Public account numbers and internal IDs differ. Source discovery accepts exactly one database or REDNOTE_SOURCE_DB. Report actual local coverage, never guarantee server completeness or deleted-record recovery.

AI requests send only authorized selected-contact samples/context to the selected provider. Credentials stay server-side and never appear in logs, frontend responses, examples, or commits. Replies display Name-AI and approximate expression, not the person's real feelings. Use peer words as examples and user words as context; do not learn from previous AI outputs as if they were real.

Deletion requires the current access password, rejects active backup jobs, preserves shared assets and other contacts, clears late AI reply generations, and never changes client originals or external saved files.

Inspect callers/schema before minimal complete edits. Keep scroll anchors and handle timeout/error/contact-switch/lock/stale responses. Frontend changes need refresh; Python changes need a service restart without removing the password. Use synthetic temporary data and mock models for tests.

Every feature/style/configuration change updates both READMEs, SKILL.md, this English guide, and affected Chinese/English references. Publish only on explicit authorization after inspecting actual staged files. Do not include data/, credentials, personal paths, identities, screenshots, or third-party media. Do not invent license permissions. Report validation and actual limitations.
