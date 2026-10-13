# Architecture and data

app.py serves local HTTP; contacts.py resolves source/identity; export_rednote.py snapshots and normalizes; media.py downloads/converts; sync_job.py serializes jobs; security.py authenticates; ai_chat.py stores independent AI data; backup_delete.py removes selected archives.

REDNOTE_SOURCE_DB overrides unique discovery under ~/Library/Containers/*/Data/Documents/XYStorageCoreRoot/Common/storage.common.defaultDataBase/Files/PrivateMessage.db. Source tables are XYPMMessageUserModel, XYPMMessageChatModel, XYPMMessageMessageModel. Match peer@owner local_chat_user_id; preserve raw metadata and millisecond timestamps.

Real tables: messages(id,contact,sender,time,content,source_id), rednote_raw(source_id,contact,payload), media_assets(url,path,mime,error), rednote_contacts(public_id,peer_id,owner_id,local_id,nickname,avatar_url,contact). Native identity deduplicates by source_id; plain imports by contact/sender/time/content.

Types: 1 text,2 image,3 share,4 system,9 audio,10 recalled,11 video,13 interactive sticker,16 custom sticker,17 call. Assets use URL SHA-256 names and .m4a/.mp4 conversions. Serve only registered names with byte ranges. Source snapshots can include unrelated contacts and must not be shared as per-contact exports.

All APIs/media require authentication when enabled; POST validates Host, Origin and JSON. Backup deletion uses /api/backup/delete with contact/password. It clears selected messages/raw/AI/registration/exports/exclusive media and matching identity rows from project snapshots. Remaining raw/avatar/emoji references preserve shared assets. Original client data stays read-only. Cross-file/database cleanup is not one atomic filesystem transaction; do not claim complete rollback/forensic erasure.

Message query supports contact,q,page,start,end,at,before_time,before_id. Timeline returns target_id/target_day and a batch containing the target. Sync exit codes alone do not guarantee media completeness; inspect failed counts. Profile JSON still lacks full multi-process write safety.
