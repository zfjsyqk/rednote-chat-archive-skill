import csv, io, json, sqlite3
import media, re, security, sync_job, shutil, contacts, ai_chat, backup_delete
from http.cookies import SimpleCookie
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
ROOT = Path(__file__).resolve().parent
DB = ROOT / 'data' / 'chats.sqlite3'
DB.parent.mkdir(exist_ok=True)
def connect():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute('''CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, contact TEXT NOT NULL, sender TEXT NOT NULL, time TEXT NOT NULL, content TEXT NOT NULL, UNIQUE(contact,sender,time,content))''')
    return c
with connect() as c: media.init(c)
class Handler(BaseHTTPRequestHandler):
    def reply(self, value, status=200):
        raw=json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(raw)
    def token(self):
        cookie=SimpleCookie()
        try:cookie.load(self.headers.get('Cookie',''))
        except Exception:return ''
        return cookie['chat_session'].value if 'chat_session' in cookie else ''
    def allowed(self):
        return security.authenticated(self.token())
    def cookie_reply(self,token):
        raw=b'{"ok":true}'
        self.send_response(200);self.send_header('Content-Type','application/json')
        self.send_header('Set-Cookie',f'chat_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={28800 if token else 0}')
        self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
    def host_ok(self):
        return self.headers.get('Host','').split(':')[0] in ('127.0.0.1','localhost')
    def do_GET(self):
        if not self.host_ok():return self.reply({'error':'无效主机'},403)
        u=urlparse(self.path); q=parse_qs(u.query)
        if u.path=='/api/auth/status':return self.reply({'enabled':security.enabled(),'locked':not self.allowed()})
        if (u.path.startswith('/api/') or u.path.startswith('/media/')) and not self.allowed():return self.reply({'error':'请先解锁'},401)
        if u.path.startswith('/api/'):
            with connect() as c:
                if u.path=='/api/ai/settings':return self.reply(ai_chat.public_settings())
                if u.path=='/api/ai/messages':return self.reply(ai_chat.history(q.get('contact',[''])[0]))
                if u.path=='/api/config':
                    path=ROOT/'data/profiles.json'
                    value=json.loads(path.read_text()) if path.exists() else {'avatars':{},'emojis':{}}
                    value['downloadDir']=str(Path.home()/'Downloads');return self.reply(value)
                if u.path=='/api/sync-status':return self.reply(sync_job.status())
                if u.path=='/api/timeline':
                    return self.reply([dict(r) for r in c.execute("SELECT substr(time,1,10) AS day,count(*) AS count FROM messages WHERE contact=? GROUP BY day ORDER BY day DESC",(q.get('contact',[''])[0],))])
                if u.path=='/api/media-status':
                    return self.reply({'cached':c.execute('SELECT count(*) FROM media_assets WHERE path IS NOT NULL').fetchone()[0], 'failed':c.execute('SELECT count(*) FROM media_assets WHERE path IS NULL').fetchone()[0]})
                if u.path=='/api/contacts':
                    return self.reply([dict(r) for r in c.execute('SELECT contact,count(*) AS count,max(time) AS latest FROM messages GROUP BY contact ORDER BY latest DESC')])
                if u.path=='/api/messages':
                    contact=q.get('contact',[''])[0]; term=q.get('q',[''])[0]
                    page=max(0,int(q.get('page',['0'])[0]))
                    where='contact=? AND instr(lower(content),lower(?))>0'; args=[contact,term]
                    start=q.get('start',[''])[0];end=q.get('end',[''])[0]
                    if start:where+=' AND time>=?';args.append(start)
                    if end:where+=' AND time<?';args.append(end+' 99')
                    at=q.get('at',[''])[0]
                    target=None;offset=None
                    if at:
                        target=c.execute('SELECT id,time FROM messages WHERE '+where+' AND time>=? ORDER BY time,id LIMIT 1',args+[at]).fetchone()
                        if not target:target=c.execute('SELECT id,time FROM messages WHERE '+where+' ORDER BY time DESC,id DESC LIMIT 1',args).fetchone()
                        if target:
                            rank=c.execute('SELECT count(*) FROM messages WHERE '+where+' AND (time>? OR (time=? AND id>?))',args+[target['time'],target['time'],target['id']]).fetchone()[0]
                            offset=max(0,rank-199);page=offset//200
                    total=c.execute('SELECT count(*) FROM messages WHERE '+where,args).fetchone()[0]
                    page=min(page,max(0,(total-1)//200))
                    before=q.get('before_time',[''])[0];before_id=q.get('before_id',['0'])[0]
                    if before:
                        rows=c.execute('SELECT * FROM messages WHERE '+where+' AND (time<? OR (time=? AND id<?)) ORDER BY time DESC,id DESC LIMIT 200',args+[before,before,int(before_id)]).fetchall()
                    else:
                        rows=c.execute('SELECT * FROM messages WHERE '+where+' ORDER BY time DESC,id DESC LIMIT 200 OFFSET ?',args+[offset if offset is not None else page*200]).fetchall()
                    cursor={'time':rows[-1]['time'],'id':rows[-1]['id']} if rows else None
                    has_more=bool(cursor and c.execute('SELECT 1 FROM messages WHERE '+where+' AND (time<? OR (time=? AND id<?)) LIMIT 1',args+[cursor['time'],cursor['time'],cursor['id']]).fetchone())
                    result=[]
                    for row in rows:
                        item=dict(row); item['media']=[]
                        if item.get('source_id'):
                            raw=c.execute('SELECT payload FROM rednote_raw WHERE source_id=?',(item['source_id'],)).fetchone()
                            if raw:
                                original=json.loads(raw[0]);item['content_type']=original['content_type']
                                if original['content_type']==3:
                                    try:
                                        shared=json.loads(original['content']);author=shared.get('user') or {}
                                        item['share']={'title':shared.get('title') or shared.get('desc') or '分享的笔记','link':shared.get('link') or '', 'author':author.get('nickname') or '', 'video':str(shared.get('noteType','')).lower() in ('video','1')}
                                    except (ValueError,TypeError,AttributeError):pass
                                for asset in media.assets(original):
                                    cached=c.execute('SELECT path,error FROM media_assets WHERE url=?',(asset['url'],)).fetchone()
                                    asset['src']='/media/'+cached['path'] if cached and cached['path'] else None
                                    asset['error']=cached['error'] if cached else '附件尚未备份'
                                    mime=c.execute('SELECT mime FROM media_assets WHERE url=?',(asset['url'],)).fetchone()
                                    asset['mime']=mime[0] if mime else None
                                    item['media'].append(asset)
                        result.append(item)
                    return self.reply({'total':total,'page':page,'messages':result,'cursor':cursor,'has_more':has_more,'target_id':target['id'] if target else None,'target_day':target['time'][:10] if target else None})
                if u.path=='/api/export':
                    return self.reply([dict(r) for r in c.execute('SELECT contact,sender,time,content FROM messages ORDER BY contact,time,id')])
            return self.reply({'error':'不存在的接口'},404)
        if u.path.startswith('/media/'):
            name=u.path[7:]
            if not re.fullmatch(r'[a-f0-9]{64}(?:\.(?:m4a|mp4))?',name): return self.reply({'error':'无效文件'},404)
            path=ROOT/'data/media'/name
            if not path.is_file(): return self.reply({'error':'附件不存在'},404)
            with connect() as c:
                row=c.execute('SELECT mime FROM media_assets WHERE path=?',(name,)).fetchone()
            if not row:return self.reply({'error':'附件未登记'},404)
            size=path.stat().st_size;start=0;end=size-1;partial=False
            header=self.headers.get('Range')
            if header:
                match=re.fullmatch(r'bytes=(\d*)-(\d*)',header)
                if not match or not any(match.groups()):return self.reply({'error':'无效范围'},416)
                a,b=match.groups()
                if a:start=int(a);end=min(int(b),end) if b else end
                else:start=max(0,size-int(b))
                if start>end or start>=size:
                    self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.end_headers();return
                partial=True
            self.send_response(206 if partial else 200)
            self.send_header('Content-Type',row['mime'] or 'application/octet-stream')
            self.send_header('Cache-Control','no-store');self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-start+1))
            if partial:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
            self.end_headers()
            try:
                with path.open('rb') as f:
                    f.seek(start);remaining=end-start+1
                    while remaining:
                        chunk=f.read(min(65536,remaining))
                        if not chunk:break
                        self.wfile.write(chunk);remaining-=len(chunk)
            except (BrokenPipeError,ConnectionResetError):pass
            return
        name={'/':'index.html' ,'/app.js':'app.js','/style.css':'style.css'}.get(u.path)
        if not name: return self.reply({'error':'找不到页面'},404)
        raw=(ROOT/'static'/name).read_bytes()
        self.send_response(200); self.send_header('Content-Type',{'html':'text/html; charset=utf-8','js':'text/javascript; charset=utf-8','css':'text/css; charset=utf-8'}[name.rsplit('.',1)[1]]); self.send_header('Content-Length',str(len(raw))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(raw)
    def do_POST(self):
        if not self.host_ok():return self.reply({'error':'无效主机'},403)
        origin=self.headers.get('Origin')
        if origin and origin!='http://'+self.headers.get('Host',''):return self.reply({'error':'不允许跨站请求'},403)
        if 'application/json' not in self.headers.get('Content-Type',''):return self.reply({'error':'需要JSON请求'},415)
        if self.path!='/api/import':
            try:
                length=int(self.headers.get('Content-Length','0'))
                if length>65536:raise ValueError('请求过大')
                body=json.loads(self.rfile.read(length))
                if self.path=='/api/auth/login':
                    return self.cookie_reply(security.login(str(body.get('password','')),self.client_address[0]))
                if not self.allowed():return self.reply({'error':'请先解锁'},401)
                if self.path=='/api/auth/password':
                    if security.enabled() and not security.check(str(body.get('current',''))):raise ValueError('当前密码不正确')
                    security.set_password(str(body.get('password','')))
                    return self.cookie_reply(security.session())
                if self.path=='/api/auth/lock':
                    with security.LOCK:security.SESSIONS.pop(self.token(),None)
                    return self.cookie_reply('')
                if self.path=='/api/ai/settings':return self.reply(ai_chat.configure(body))
                if self.path=='/api/backup/delete':
                    if not security.enabled():raise ValueError('请先在系统设置中设置密码，再删除聊天备份')
                    token=security.login(str(body.get('password','')),self.client_address[0])
                    with security.LOCK:security.SESSIONS.pop(token,None)
                    return self.reply(backup_delete.delete(ROOT,DB,str(body.get('contact',''))))
                if self.path=='/api/ai/delete':ai_chat.delete(str(body.get('contact','')));return self.reply({'ok':True})
                if self.path=='/api/ai/send':return self.reply(ai_chat.send(DB,str(body.get('contact','')),body.get('text','')))
                if self.path=='/api/add-contact':return self.reply(sync_job.start(user_id=body.get('user_id','')))
                if self.path=='/api/sync':return self.reply(sync_job.start(body.get('contact','')))
                if self.path=='/api/save':
                    name=body.get('file','')
                    with connect() as c:row=c.execute('SELECT path FROM media_assets WHERE path=?',(name,)).fetchone()
                    if not row:raise ValueError('附件不存在')
                    dest=Path(body.get('destination','')).expanduser()
                    if not dest.is_absolute() or not dest.name:raise ValueError('请输入完整的绝对路径')
                    if not dest.parent.is_dir():raise ValueError('目标文件夹不存在')
                    with (ROOT/'data/media'/name).open('rb') as src,dest.open('xb') as out:shutil.copyfileobj(src,out)
                    return self.reply({'saved':str(dest)})
                return self.reply({'error':'找不到接口'},404)
            except (ValueError,TypeError,OSError) as e:return self.reply({'error':str(e)},400)
        if not self.allowed():return self.reply({'error':'请先解锁'},401)
        if self.headers.get('Origin') and self.headers['Origin']!='http://'+self.headers.get('Host',''): return self.reply({'error':'不允许跨站导入'},403)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>20*1024*1024: raise ValueError('文件上限为 20MB，请分批导入')
            body=json.loads(self.rfile.read(length)); raw=body['text'].lstrip('\ufeff')
            rows=json.loads(raw) if body['format']=='json' else list(csv.DictReader(io.StringIO(raw)))
            if isinstance(rows,dict): rows=rows.get('messages')
            if not isinstance(rows,list): raise ValueError('需要消息数组，或包含 messages 数组的对象')
            clean=[]
            for i,r in enumerate(rows):
                if not isinstance(r,dict): raise ValueError(f'第 {i+1} 行不是消息对象')
                vals=[r.get(k,body.get('contact','') if k=='contact' else '') for k in ('contact','sender','time','content')]
                if any(not isinstance(v,str) for v in vals): raise ValueError(f'第 {i+1} 行字段必须是文字')
                if any(not v.strip() for v in vals[:3]): raise ValueError(f'第 {i+1} 行缺少 contact、sender 或 time')
                clean.append(tuple(vals))
            with connect() as c:
                before=c.total_changes; c.executemany('INSERT OR IGNORE INTO messages(contact,sender,time,content) VALUES(?,?,?,?)',clean); added=c.total_changes-before
            self.reply({'added':added,'duplicates':len(clean)-added})
        except (ValueError,KeyError,TypeError) as e: self.reply({'error':str(e)},400)
if __name__=='__main__':
    ai_chat.start_cleaner()
    print('本地聊天档案：http://127.0.0.1:8765',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
