import tempfile,sqlite3,json,hashlib
from pathlib import Path
import backup_delete,ai_chat,media
with tempfile.TemporaryDirectory() as folder:
 root=Path(folder);(root/'data/media').mkdir(parents=True);(root/'data/exports').mkdir();(root/'data/source-backups').mkdir()
 db=root/'data/chats.sqlite3';ai_chat.DB=root/'data/ai.sqlite3'
 urls=['https://example.test/private','https://example.test/shared'];keys=[hashlib.sha256(u.encode()).hexdigest() for u in urls]
 with sqlite3.connect(db) as c:
  c.execute('CREATE TABLE messages(contact TEXT)');c.executemany('INSERT INTO messages VALUES(?)',[('remove',),('keep',)])
  c.execute('CREATE TABLE rednote_raw(source_id TEXT,contact TEXT,payload TEXT)');media.init(c)
  c.execute('CREATE TABLE rednote_contacts(public_id TEXT,peer_id TEXT,owner_id TEXT,local_id TEXT,nickname TEXT,avatar_url TEXT,contact TEXT)')
  c.execute('INSERT INTO rednote_contacts VALUES(?,?,?,?,?,?,?)',('123','b'*24,'a'*24,'local','name','','remove'))
  for i,(contact,url) in enumerate([('remove',urls[0]),('remove',urls[1]),('keep',urls[1])]):
   c.execute('INSERT INTO rednote_raw VALUES(?,?,?)',(str(i),contact,json.dumps({'content_type':16,'content':json.dumps({'url':url})})))
  for url,key in zip(urls,keys):c.execute('INSERT INTO media_assets VALUES(?,?,?,?)',(url,key,'image/png',None));(root/'data/media'/key).write_bytes(b'test')
 for name,contact in [('remove','remove'),('keep','keep')]: (root/'data/exports'/(name+'.json')).write_text(json.dumps({'contact':contact}))
 with sqlite3.connect(root/'data/source-backups/test.sqlite3') as c:
  c.execute('CREATE TABLE messages(local_chat_user_id TEXT)');c.executemany('INSERT INTO messages VALUES(?)',[('local',),('other',)])
 with ai_chat.connect() as c:c.executemany('INSERT INTO messages(contact,role,content,created) VALUES(?,?,?,?)',[('remove','user','x',1),('keep','user','y',1)])
 backup_delete.delete(root,db,'remove')
 with sqlite3.connect(db) as c:
  assert c.execute('SELECT contact FROM messages').fetchall()==[('keep',)]
  assert c.execute('SELECT contact FROM rednote_raw').fetchall()==[('keep',)]
 assert not (root/'data/media'/keys[0]).exists() and (root/'data/media'/keys[1]).exists()
 assert not (root/'data/exports/remove.json').exists() and (root/'data/exports/keep.json').exists()
 with sqlite3.connect(root/'data/source-backups/test.sqlite3') as c:assert c.execute('SELECT * FROM messages').fetchall()==[('other',)]
 with ai_chat.connect() as c:assert [r[0] for r in c.execute('SELECT contact FROM messages')]==['keep']
print('PASS: selected backup removed; shared attachments and other conversation retained')
