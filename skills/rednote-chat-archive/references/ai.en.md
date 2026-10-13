# AI behavior

AI data uses data/ai_chats.sqlite3; provider configuration uses data/ai_config.json (0600). Independent provider/model/key settings support OpenAI Responses (store:false) and DeepSeek Chat Completions (thinking disabled). Keys are never returned to browsers; empty inputs preserve them; environment keys are supported. Defaults are editable, not guaranteed for every account.

Only authorized selected-contact historical samples and recent AI context go to the selected provider. Compute peer style statistics and select recent/history-spanning/relevant peer text, using prior user turns as context. AI outputs are not real style examples. Replies carry Name-AI and do not represent the person's present feelings.

Persist successful user/assistant pairs only. Pending UI placeholders stay out of databases. Deletion increments contact generations to reject late replies. Bound model calls (45s server deadline,60s frontend) and report key/quota/rate/network failures. API costs are separate from ChatGPT subscriptions.

Retention options are 1,7,30,60 days or permanent (0), default1. Expiry uses creation time; cleanup at startup/read/configuration and every30s while running. Closed services do not run timers. Changes immediately remove expired rows. secure_delete is not a promise of forensic erasure across disks/backups. Tests use temporary databases and mocks for isolation,retention,provider routing,timeouts/deletion races; no paid private-history tests without explicit authorization.
