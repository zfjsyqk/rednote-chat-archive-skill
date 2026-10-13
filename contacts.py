"""Resolve only identities present in the local client's records/cache."""
import json,re,sqlite3,gzip,os
import urllib.request,urllib.error,urllib.parse
from pathlib import Path
def source_path():
 configured=os.environ.get('REDNOTE_SOURCE_DB')
 if configured:return Path(configured).expanduser().resolve()
 pattern='*/Data/Documents/XYStorageCoreRoot/Common/storage.common.defaultDataBase/Files/PrivateMessage.db'
 found=list((Path.home()/'Library/Containers').glob(pattern))
 if len(found)==1:return found[0]
 return Path.home()/'Library/Containers/UNCONFIGURED/Data/Documents/XYStorageCoreRoot/Common/storage.common.defaultDataBase/Files/PrivateMessage.db'
SOURCE=source_path()
DB=Path(__file__).resolve().parent/'data/chats.sqlite3'
def init(c):
 c.execute('CREATE TABLE IF NOT EXISTS rednote_contacts(public_id TEXT PRIMARY KEY,peer_id TEXT,owner_id TEXT,local_id TEXT,nickname TEXT,avatar_url TEXT,contact TEXT UNIQUE)')
def cached_uid(public_id):
 cache=SOURCE.parents[5]/'Library/Caches/com.xingin.discover/Cache.db'
 if not cache.exists():return None
 def walk(v):
  if isinstance(v,dict):
   rid=next((str(v[k]) for k in ('red_id','redId','redid','red_no','redNumber','account') if k in v),None)
   uid=next((v[k] for k in ('user_id','userId','userid','id') if re.fullmatch('[a-f0-9]{24}',str(v.get(k,'')))),None)
   if rid==public_id and uid:return uid
   for x in v.values():
    found=walk(x)
    if found:return found
  elif isinstance(v,list):
   for x in v:
    found=walk(x)
    if found:return found
 try:
  with sqlite3.connect(cache.as_uri()+'?mode=ro',uri=True) as c:
   for on_disk,raw in c.execute('SELECT isDataOnFS,receiver_data FROM cfurl_cache_receiver_data'):
    try:
     if on_disk:
      name=raw.decode('utf-8') if isinstance(raw,bytes) else str(raw)
      if Path(name).name!=name:continue
      raw=(cache.parent/'fsCachedData'/name).read_bytes()
     if isinstance(raw,bytes) and raw.startswith(b'\x1f\x8b'):raw=gzip.decompress(raw)
     found=walk(json.loads(raw))
     if found:return found
    except (ValueError,TypeError,OSError):pass
 except sqlite3.Error:pass
 return None

def profile_uid(value):
 match=re.search(r'https://(?:www\.)?xiaohongshu\.com/user/profile/([a-f0-9]{24})(?:[/?#\s]|$)',value)
 if match:return match.group(1)
 short=re.search(r'https://(?:xhslink\.cn|xhslink\.com)/[A-Za-z0-9/_-]+',value)
 if not short:return None
 class Redirect(urllib.request.HTTPRedirectHandler):
  def redirect_request(self,req,fp,code,msg,headers,newurl):return None
 try:
  with urllib.request.build_opener(Redirect).open(urllib.request.Request(short.group(0),headers={'User-Agent':'Mozilla/5.0'}),timeout=15) as response:
   location=response.geturl()
 except urllib.error.HTTPError as e:
  if e.code not in (301,302,303,307,308):raise ValueError('主页分享链接访问失败，请复制完整主页链接') from e
  location=urllib.parse.urljoin(short.group(0),e.headers.get('Location',''))
 except (OSError,ValueError) as e:raise ValueError('主页分享链接暂时无法访问，请检查网络或使用完整主页链接') from e
 parsed=urllib.parse.urlsplit(location)
 match=re.fullmatch(r'/user/profile/([a-f0-9]{24})/?',parsed.path)
 if parsed.hostname not in ('www.xiaohongshu.com','xiaohongshu.com') or not match:
  raise ValueError('分享链接没有跳转到用户主页，请复制用户主页分享链接')
 return match.group(1)

def resolve(value):
 value=str(value).strip()
 uid_from_link=profile_uid(value)
 if uid_from_link:value=uid_from_link
 if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',value):raise ValueError('请输入小红书号、内部用户ID或用户主页分享链接')
 with sqlite3.connect(DB) as c:
  init(c)
  row=c.execute('SELECT public_id,peer_id,owner_id,local_id,nickname,avatar_url,contact FROM rednote_contacts WHERE public_id=? OR peer_id=?',(value,value)).fetchone()
  if row:return dict(zip(('public_id','peer_id','owner_id','local_id','nickname','avatar_url','contact'),row))
 with sqlite3.connect(SOURCE.as_uri()+'?mode=ro',uri=True) as c:
  c.row_factory=sqlite3.Row
  users=c.execute('SELECT * FROM XYPMMessageUserModel').fetchall()
  uid=value if re.fullmatch('[a-f0-9]{24}',value) else None
  if not uid:
   matches=[u for u in users if any(str(u[k] or '')==value for k in ('accountName','record_id') if k in u.keys())]
   if len(matches)==1:uid=matches[0]['user_id']
  if not uid:uid=cached_uid(value)
  user=next((u for u in users if u['user_id']==uid),None)
  if not user:raise ValueError('本地尚未找到这个小红书号。请先在 Mac 小红书打开对方主页及聊天后重试；仍无法识别时，可粘贴对方主页分享链接（含内部用户ID）。')
  chat=c.execute('SELECT * FROM XYPMMessageChatModel WHERE chat_id=?',(uid,)).fetchall()
  if len(chat)!=1:raise ValueError('本地没有唯一可识别的聊天会话，请先打开对方聊天')
  chat=chat[0];local=chat['local_chat_user_id'];owner=chat['ownerUserId'] or local.split('@')[-1]
  nickname=user['nickname'] or chat['nickname'] or value
  return {'public_id':value,'peer_id':uid,'owner_id':owner,'local_id':local,'nickname':nickname,'avatar_url':user['avatar'] or '', 'contact':nickname+' · '+value}
def registered(contact):
 with sqlite3.connect(DB) as c:
  init(c);c.row_factory=sqlite3.Row
  r=c.execute('SELECT * FROM rednote_contacts WHERE contact=?',(contact,)).fetchone()
  if not r:raise ValueError('此会话尚未配置小红书数据来源')
  return dict(r)
def save(target):
 with sqlite3.connect(DB) as c:
  init(c);c.execute('INSERT OR REPLACE INTO rednote_contacts VALUES(?,?,?,?,?,?,?)',tuple(target[k] for k in ('public_id','peer_id','owner_id','local_id','nickname','avatar_url','contact')))
