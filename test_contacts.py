import tempfile,sqlite3,json
from pathlib import Path
import app,contacts,export_rednote
with tempfile.TemporaryDirectory() as folder:
 root=Path(folder);src=root/'source.db';db=sqlite3.connect(src)
 db.executescript('CREATE TABLE XYPMMessageUserModel(__objectID TEXT,user_id TEXT,local_user_id TEXT,nickname TEXT,record_id TEXT,accountName TEXT,avatar TEXT); CREATE TABLE XYPMMessageChatModel(__objectID TEXT,chat_id TEXT,local_chat_user_id TEXT,ownerUserId TEXT,nickname TEXT); CREATE TABLE XYPMMessageMessageModel(__objectID TEXT,local_message_id TEXT,message_id TEXT,uuid TEXT,local_chat_user_id TEXT,content_type INTEGER,sender_id TEXT,receiver_id TEXT,content TEXT,create_time INTEGER,store_id INTEGER);')
 owner='a'*24
 for n in (1,2):
  peer=str(n)*24;local=peer+'@'+owner
  db.execute('INSERT INTO XYPMMessageUserModel(__objectID,user_id,local_user_id,nickname,record_id) VALUES(?,?,?,?,?)',(str(n),peer,local,'测试'+str(n),'12345678'+str(n)))
  db.execute('INSERT INTO XYPMMessageChatModel(__objectID,chat_id,local_chat_user_id,ownerUserId,nickname) VALUES(?,?,?,?,?)',(str(n),peer,local,owner,'测试'+str(n)))
  db.execute('INSERT INTO XYPMMessageMessageModel(__objectID,local_message_id,message_id,local_chat_user_id,content_type,sender_id,content,create_time) VALUES(?,?,?,?,?,?,?,?)',(str(n),str(n),str(n),local,1,owner,'测试消息'+str(n),1791737579601))
 db.commit();db.close();app.DB=root/'chats.db';contacts.DB=app.DB;contacts.SOURCE=src;export_rednote.SOURCE=src;export_rednote.ROOT=root
 for n in (1,2):
  target=contacts.resolve('12345678'+str(n));assert target['peer_id']==str(n)*24
  export_rednote.run(target)
  assert contacts.registered(target['contact'])['public_id']=='12345678'+str(n)
 with app.connect() as c:
  rows=c.execute('SELECT contact,sender,content FROM messages ORDER BY contact').fetchall()
  assert len(rows)==2 and all(r['sender']=='我' for r in rows)
  assert rows[0]['contact']!=rows[1]['contact']
 try:contacts.resolve('unknown-id')
 except ValueError:pass
 else:raise AssertionError('unknown identity should fail')
 print('PASS: multiple IDs resolve, export separately, register, and unknown IDs fail safely')
from unittest.mock import patch
import urllib.error
from email.message import Message
headers=Message();headers['Location']='https://www.xiaohongshu.com/user/profile/'+'b'*24+'?token=example'
with patch('urllib.request.OpenerDirector.open',side_effect=urllib.error.HTTPError('https://xhslink.cn/o/test',302,'Found',headers,None)):
 assert contacts.profile_uid('分享文案 https://xhslink.cn/o/test')=='b'*24
headers['Location']='https://example.com/user/profile/'+'b'*24
bad=Message();bad['Location']='https://example.com/user/profile/'+'b'*24
with patch('urllib.request.OpenerDirector.open',side_effect=urllib.error.HTTPError('https://xhslink.cn/o/test',302,'Found',bad,None)):
 try:contacts.profile_uid('https://xhslink.cn/o/test')
 except ValueError:pass
 else:raise AssertionError('untrusted redirect should fail')
print('PASS: shared text resolves first redirect and rejects unrelated domains')
