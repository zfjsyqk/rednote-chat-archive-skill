"""Read-only snapshot and export of a selected local conversation."""
import json, sqlite3
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import app, contacts, argparse, media
ROOT=Path(__file__).resolve().parent
SOURCE=contacts.SOURCE
TZ=ZoneInfo('Asia/Shanghai')
def display(r,owner):
    raw=r['content'] or ''
    t=int(r['content_type'] or 0)
    if t==1: return raw
    try: d=json.loads(raw)
    except (ValueError,TypeError): return raw or '[空消息]'
    if not isinstance(d,dict): return raw
    label={2:'图片',3:'分享',4:'系统消息',9:'语音',10:'撤回提示',11:'视频',13:'互动表情',16:'表情',17:'通话'}.get(t,'其他消息')
    parts=['['+label+']']
    if t==17:
        value=d.get('senderContent' if r['sender_id']==owner else 'receiverContent')
        if value: parts.append(str(value))
    else:
        for key in ('title','desc','content','duration','link','url','videoLink'):
            value=d.get(key)
            if value is not None and value!='': parts.append((key+': ' if key=='duration' else '')+str(value))
    if r.get('voiceText'): parts.append('转写：'+r['voiceText'])
    if len(parts)==1: parts.append(json.dumps(d,ensure_ascii=False))
    return '\n'.join(parts)
def run(target):
    contact=target["contact"];peer=target["peer_id"];owner=target["owner_id"];nickname=target["nickname"]
    filename=target["public_id"]
    folder=ROOT/'data'/'exports'; folder.mkdir(parents=True,exist_ok=True)
    snap=ROOT/'data'/'source-backups'/('PrivateMessage-'+datetime.now(TZ).strftime('%Y%m%d-%H%M%S-%f')+'.sqlite3');snap.parent.mkdir(exist_ok=True)
    with sqlite3.connect(SOURCE.as_uri()+'?mode=ro',uri=True) as src, sqlite3.connect(snap) as dst: src.backup(dst)
    c=sqlite3.connect(snap);c.row_factory=sqlite3.Row
    rows=[dict(r) for r in c.execute('SELECT * FROM XYPMMessageMessageModel WHERE local_chat_user_id=? ORDER BY create_time,store_id', (target['local_id'],))]
    if not rows: raise RuntimeError('未找到目标聊天；未写入查看器')
    messages=[]
    for r in rows:
        ms=r['create_time']
        stamp=datetime.fromtimestamp(ms/1000,TZ).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        messages.append({'contact':contact,'sender':'我' if r['sender_id']==owner else nickname,'time':stamp,'content':display(r,owner)})
    (folder/(filename+'.raw.json')).write_text(json.dumps({'contact':contact,'internal_user_id':peer,'messages':rows},ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/(filename+'.json')).write_text(json.dumps(messages,ensure_ascii=False,indent=2),encoding='utf-8')
    with app.connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS rednote_raw (source_id TEXT PRIMARY KEY, contact TEXT, payload TEXT NOT NULL)')
        if 'source_id' not in [r[1] for r in db.execute('PRAGMA table_info(messages)')]:
            db.execute('ALTER TABLE messages RENAME TO messages_legacy')
            db.execute('CREATE TABLE messages(id INTEGER PRIMARY KEY,contact TEXT NOT NULL,sender TEXT NOT NULL,time TEXT NOT NULL,content TEXT NOT NULL,source_id TEXT)')
            db.execute('INSERT INTO messages(id,contact,sender,time,content) SELECT id,contact,sender,time,content FROM messages_legacy')
            db.execute('DROP TABLE messages_legacy')
            db.execute('CREATE UNIQUE INDEX imported_message_identity ON messages(contact,sender,time,content) WHERE source_id IS NULL')
            db.execute('CREATE UNIQUE INDEX source_message_identity ON messages(source_id) WHERE source_id IS NOT NULL')
        db.execute('DELETE FROM messages WHERE contact=? AND source_id IS NULL',(contact,))
        for r,m in zip(rows,messages):
            key=r['message_id'] or r['uuid'] or r['local_message_id'] or r['__objectID']
            db.execute('INSERT OR REPLACE INTO rednote_raw VALUES(?,?,?)',(key,contact,json.dumps(r,ensure_ascii=False)))
            db.execute('INSERT INTO messages(contact,sender,time,content,source_id) VALUES(?,?,?,?,?) ON CONFLICT(source_id) WHERE source_id IS NOT NULL DO UPDATE SET contact=excluded.contact,sender=excluded.sender,time=excluded.time,content=excluded.content',tuple(m[k] for k in ('contact','sender','time','content'))+(key,))
        count=db.execute('SELECT count(*) FROM messages WHERE contact=?',(contact,)).fetchone()[0]
    summary={'contact':contact,'records':len(rows),'viewer_records':count,'earliest':messages[0]['time'],'latest':messages[-1]['time'],'timezone':'Asia/Shanghai','snapshot':str(snap),'attachments':'原始元数据和链接已保存；附件备份状态见 data/media/report.json','completeness':'仅包括 Mac 当前本地数据库中的记录，未验证完整历史'}
    (folder/(filename+'.report.json')).write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    if target.get('avatar_url'):
        media.FOLDER.mkdir(parents=True,exist_ok=True)
        record=media.fetch({'kind':'image','url':target['avatar_url']})
        if record[1]:
            with app.connect() as db:
                media.init(db);db.execute('INSERT OR REPLACE INTO media_assets VALUES(?,?,?,?)',record)
            path=ROOT/'data/profiles.json'
            profiles=json.loads(path.read_text()) if path.exists() else {'avatars':{},'emojis':{}}
            profiles['avatars'][contact]='/media/'+record[1]
            profiles['avatars'][nickname]='/media/'+record[1]
            path.write_text(json.dumps(profiles,ensure_ascii=False))
    contacts.save(target)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--user',required=True);args=parser.parse_args();run(contacts.resolve(args.user))
