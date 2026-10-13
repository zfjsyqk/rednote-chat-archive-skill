# Product and interaction

The Chinese sidebar lists contacts, avatars, counts, add/import/settings/lock actions. More menu labels are 更新备份 (Update backup), 导出备份 (Export backup), 删除AI记录 (Delete AI records), 删除备份 (Delete backup). Use outline SVG icons, content-sized rounded white panels, symmetric 6px panel/14px item padding, soft shadows, gray item hover, red backup deletion; the three-dot trigger stays transparent. Outside clicks/Escape close the menu.

White chat background, blue outgoing/gray incoming bubbles, circular avatars, 14px text/input. Copy/save buttons sit outside bubbles and align vertically. Standalone stickers fit 100px with preserved ratio and large-image previews. Inline local RedNote emoji fall back to system emoji when missing. Center system notices without avatars; calls show phone icon/state; share cards show cover/title/author/video marker and open the source link.

Chronological messages open at latest. Scroll upward loads older batches of 200 preserving the anchor. Timeline targets the first real message on a selected day, resets search/date filters, and reports the actual fallback day. AI is separate at the tail and excluded from real search/export/timeline. Times use Asia/Shanghai/Monday weeks: today clock only, same-week weekday+clock, otherwise YYYY-MM-DD+clock.

AI replies show Name-AI, user messages have no AI badge. Sending inserts immediate pending user/assistant avatar placeholders, replaced on success. Failure shows an error and restores the draft. Delete backup requires current-password confirmation (set a password first if absent), is irreversible in the app, retains shared/other records, and leaves client originals/external files untouched. Confirm/cancel spacing is 12px.

README screenshots live in docs/screenshots/chat-view.jpg and conversation-menu.jpg. Reproduce via demo_preview.py on port8770 using only fictional contacts/DEMO identifiers/generated avatars/mock AI. The preview rejects POST and does not read production data or call model services.
