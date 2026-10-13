import json, hashlib, sqlite3, urllib.request, subprocess, mimetypes, ssl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
ROOT=Path(__file__).resolve().parent
FOLDER=ROOT/'data/media'
TLS=ssl.create_default_context()
def assets(row):
 try: d=json.loads(row['content'] or '')
 except ValueError:return []
 if not isinstance(d,dict):return []
 t=int(row['content_type'] or 0); out=[]
 def add(kind,url):
  if isinstance(url,str) and url.startswith(('https://','http://')):out.append({'kind':kind,'url':url,'width':d.get('size',{}).get('width') or d.get('width'),'height':d.get('size',{}).get('height') or d.get('height')})
 if t==2:add('image',d.get('imageDataMap',{}).get('IM_ORG',{}).get('url') or d.get('link'))
 elif t==3:
  add('share-cover',d.get('cover') or d.get('image'))
  add('share-avatar',d.get('user',{}).get('image'))
 elif t==9:add('audio',d.get('link'))
 elif t==11:
  add('video',d.get('originalVideoLink') or d.get('videoLink'));add('poster',d.get('imageDataMap',{}).get('IM_PRV',{}).get('url') or d.get('link'))
 elif t==13:add('sticker',d.get('image'))
 elif t==16:add('sticker',d.get('url') or d.get('thumb',{}).get('url'))
 return out

def init(c):
 c.execute('CREATE TABLE IF NOT EXISTS media_assets(url TEXT PRIMARY KEY, path TEXT, mime TEXT, error TEXT)')
def fetch(item):
 url=item['url']; key=hashlib.sha256(url.encode()).hexdigest(); target=FOLDER/key
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.xiaohongshu.com/'})
  with urllib.request.urlopen(req,timeout=60,context=TLS) as r:
   mime=r.headers.get_content_type();raw=r.read(150*1024*1024+1)
  if len(raw)>150*1024*1024:raise ValueError('超过150MB')
  if not raw:raise ValueError('附件为空')
  if mime=='text/html':raise ValueError('服务器返回网页而不是附件')
  target.write_bytes(raw)
  if item['kind']=='audio':
   converted=FOLDER/(key+'.m4a')
   result=subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-i',str(target),'-vn','-c:a','aac',str(converted)],capture_output=True,timeout=90)
   if result.returncode:raise ValueError('音频转换失败')
   target=converted;mime='audio/mp4'
  elif item['kind'] in ('image','sticker','poster','share-cover','share-avatar'):
   if raw.startswith(b'\x89PNG'):mime='image/png'
   elif raw.startswith(b'\xff\xd8'):mime='image/jpeg'
   elif raw.startswith(b'GIF8'):mime='image/gif'
   elif raw[:4]==b'RIFF':mime='image/webp'
   elif raw.lstrip().startswith(b'{'):raise ValueError('附件为动画描述数据，暂不能作为图片显示')
  elif item['kind']=='video':
   converted=FOLDER/(key+'.mp4')
   result=subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-i',str(target),'-c:v','libx264','-threads','2','-preset','fast','-crf','22','-c:a','aac','-movflags','+faststart',str(converted)],capture_output=True,timeout=300)
   if result.returncode:raise ValueError('视频转换失败')
   target=converted;mime='video/mp4'
  return (url,target.name,mime,None)
 except Exception as e:return (url,None,None,type(e).__name__+': '+str(e).split(url)[0][:160])

def run():
 FOLDER.mkdir(parents=True,exist_ok=True)
 c=sqlite3.connect(ROOT/'data/chats.sqlite3');init(c)
 rows=c.execute('SELECT payload FROM rednote_raw').fetchall();unique={}
 for (payload,) in rows:
  for a in assets(json.loads(payload)):unique.setdefault(a['url'],a)
 existing={r[0] for r in c.execute('SELECT url,path FROM media_assets WHERE path IS NOT NULL') if (FOLDER/r[1]).is_file()}
 pending=[a for u,a in unique.items() if u not in existing]
 print(f'附件共 {len(unique)} 个，已缓存 {len(existing)} 个，待下载 {len(pending)} 个',flush=True)
 done=0
 with ThreadPoolExecutor(max_workers=16) as pool:
  for f in as_completed([pool.submit(fetch,a) for a in pending]):
   c.execute('INSERT OR REPLACE INTO media_assets VALUES(?,?,?,?)',f.result());c.commit();done+=1
   if done%50==0:print(f'已处理 {done}/{len(pending)}',flush=True)
 stats={'total':len(unique),'cached':c.execute('SELECT count(*) FROM media_assets WHERE path IS NOT NULL').fetchone()[0],'failed':c.execute('SELECT count(*) FROM media_assets WHERE path IS NULL').fetchone()[0]}
 (FOLDER/'report.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2));print(stats,flush=True)
if __name__=='__main__':run()
