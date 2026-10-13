"""Screenshot-only preview: synthetic records, no client database or API calls."""
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parent
CONTACT='林小满 · DEMO-001'
ROWS=[('林小满','今天想去公园走走，你有空吗？'),('我','有空！我带相机，一起拍点照片吧。'),('林小满','好呀，下午三点见～[微笑R]'),('我','这份周末计划怎么样？'),('林小满','很不错呀，先喝咖啡，再去看日落。'),('我','那就这么定啦！[比心R]')]
def avatar(letter,color):
 from urllib.parse import quote
 return 'data:image/svg+xml,'+quote(f'<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80"><rect width="80" height="80" rx="40" fill="{color}"/><text x="40" y="51" text-anchor="middle" font-size="32" fill="white">{letter}</text></svg>')
MESSAGES=[{'id':i+1,'contact':CONTACT,'sender':sender,'time':f'2026-10-13 14:{20+i:02d}:00','content':text,'media':[]} for i,(sender,text) in enumerate(ROWS[:3])]
AI=[{'id':'ai-demo-1','sender':'我','time':'2026-10-13 14:26:00','content':'如果下雨呢？','media':[],'ai':True,'role':'user'},{'id':'ai-demo-2','sender':'林小满','time':'2026-10-13 14:26:03','content':'那就换成室内咖啡馆呀，也可以聊一个下午～ ☕','media':[],'ai':True,'role':'assistant'}]
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  path=urlsplit(self.path).path
  values={'/api/auth/status':{'enabled':False,'locked':False},'/api/config':{'avatars':{CONTACT:avatar('林','#89b6a5'),'林小满':avatar('林','#89b6a5'),'我':avatar('我','#7e9fc8'),'旅行搭子 · DEMO-002':avatar('旅','#c4ab8b')},'emojis':{},'downloadDir':'/tmp'},'/api/contacts':[{'contact':CONTACT,'count':len(MESSAGES),'latest':'2026-10-13 14:25:00'},{'contact':'旅行搭子 · DEMO-002','count':12,'latest':'2026-10-12 12:00:00'}],'/api/messages':{'total':len(MESSAGES),'page':0,'messages':list(reversed(MESSAGES)),'cursor':None,'has_more':False,'target_id':None,'target_day':None},'/api/ai/messages':AI,'/api/timeline':[{'day':'2026-10-13','count':3},{'day':'2026-10-12','count':12}],'/api/media-status':{'cached':0,'failed':0},'/api/sync-status':{'running':False,'stage':'','error':None},'/api/ai/settings':{'days':1,'provider':'openai','providers':{'openai':{'model':'demo','configured':False},'deepseek':{'model':'demo','configured':False}},'configured':False,'model':'demo'}}
  if path in values:raw=json.dumps(values[path],ensure_ascii=False).encode();mime='application/json; charset=utf-8'
  elif path in ('/','/app.js','/style.css'):
   name={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[path];raw=(ROOT/'static'/name).read_bytes();mime={'/':'text/html; charset=utf-8','/app.js':'text/javascript','/style.css':'text/css'}[path]
  else:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
 def do_POST(self):self.send_error(405,'Read-only synthetic preview')
 def log_message(self,*args):pass
if __name__=='__main__':
 print('Synthetic preview http://127.0.0.1:8770 (no real data)',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8770),Handler).serve_forever()
