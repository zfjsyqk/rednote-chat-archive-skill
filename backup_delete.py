"""Remove one conversation's project backups; leave the source client untouched."""
import json,sqlite3,re,hashlib
import media,ai_chat,contacts,sync_job

def delete(root,db,contact):
 with sync_job.LOCK:
  if sync_job.STATE['running']:raise ValueError('正在备份，请等备份完成后再删除')
  with sqlite3.connect(db) as c:
   c.execute('PRAGMA secure_delete=ON')
   tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
   target=None
   if 'rednote_contacts' in tables:
    c.row_factory=sqlite3.Row
    row=c.execute('SELECT * FROM rednote_contacts WHERE contact=?',(contact,)).fetchone()
    target=dict(row) if row else None
   if not c.execute('SELECT 1 FROM messages WHERE contact=?',(contact,)).fetchone():raise ValueError('会话不存在或已删除')
   raw=[json.loads(r[0]) for r in c.execute('SELECT payload FROM rednote_raw WHERE contact=?',(contact,))] if 'rednote_raw' in tables else []
   candidates={a['url'] for r in raw for a in media.assets(r)}
   if target and target['avatar_url']:candidates.add(target['avatar_url'])
   # Full-client snapshots contain this conversation too. Remove only peer/local identity rows.
   if target:
    for path in (root/'data/source-backups').glob('*.sqlite3'):
     with sqlite3.connect(path) as snap:
      snap.execute('PRAGMA secure_delete=ON')
      for (table,) in snap.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
       if not re.fullmatch(r'\w+',table):continue
       columns=[r[1] for r in snap.execute(f'PRAGMA table_info("{table}")')]
       keys=[k for k in columns if k in ('local_chat_user_id','local_user_id','chat_id','user_id','sender_id','receiver_id')]
       if keys:snap.execute(f'DELETE FROM "{table}" WHERE '+ ' OR '.join(f'"{k}" IN (?,?)' for k in keys),[v for k in keys for v in (target['peer_id'],target['local_id'])])
   for path in (root/'data/exports').glob('*.json'):
    value=json.loads(path.read_text())
    if isinstance(value,dict) and value.get('contact')==contact:path.unlink()
    elif isinstance(value,list):
     remaining=[r for r in value if not isinstance(r,dict) or r.get('contact')!=contact]
     if len(remaining)!=len(value):
      if remaining:path.write_text(json.dumps(remaining,ensure_ascii=False))
      else:path.unlink()
   profiles_path=root/'data/profiles.json'
   profiles=json.loads(profiles_path.read_text()) if profiles_path.exists() else {'avatars':{},'emojis':{}}
   profiles.get('avatars',{}).pop(contact,None)
   if target:
    nickname=target['nickname']
    other=c.execute('SELECT 1 FROM rednote_contacts WHERE nickname=? AND contact!=?',(nickname,contact)).fetchone()
    if not other:profiles.get('avatars',{}).pop(nickname,None)
   if profiles_path.exists():profiles_path.write_text(json.dumps(profiles,ensure_ascii=False))
   ai_chat.delete(contact)
   c.execute('DELETE FROM messages WHERE contact=?',(contact,))
   if 'rednote_raw' in tables:c.execute('DELETE FROM rednote_raw WHERE contact=?',(contact,))
   if 'rednote_contacts' in tables:c.execute('DELETE FROM rednote_contacts WHERE contact=?',(contact,))
   keep_urls=set()
   if 'rednote_raw' in tables:
    for (payload,) in c.execute('SELECT payload FROM rednote_raw'):
     keep_urls.update(a['url'] for a in media.assets(json.loads(payload)))
   if 'rednote_contacts' in tables:keep_urls.update(r[0] for r in c.execute('SELECT avatar_url FROM rednote_contacts') if r[0])
   keep_paths={v.removeprefix('/media/') for group in ('avatars','emojis') for v in profiles.get(group,{}).values() if isinstance(v,str)}
   for url in candidates-keep_urls:
    row=c.execute('SELECT path FROM media_assets WHERE url=?',(url,)).fetchone()
    key=hashlib.sha256(url.encode()).hexdigest()
    paths={key,key+'.m4a',key+'.mp4'}
    if row and row[0]:paths.add(row[0])
    if paths & keep_paths:continue
    for name in paths:
     if re.fullmatch(r'[a-f0-9]{64}(?:\.(?:m4a|mp4))?',name):(root/'data/media'/name).unlink(missing_ok=True)
    c.execute('DELETE FROM media_assets WHERE url=?',(url,))
 return {'ok':True}
