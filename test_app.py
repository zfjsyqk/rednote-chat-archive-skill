import unittest,tempfile,threading,sqlite3,json,urllib.request,urllib.error,http.cookiejar
from pathlib import Path
import app,security
class AppTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();root=Path(cls.tmp.name);app.ROOT=root;app.DB=root/'test.db';security.FILE=root/'security.json'
  with app.connect() as c:
   app.media.init(c)
   c.execute('CREATE TABLE rednote_raw(source_id TEXT PRIMARY KEY,contact TEXT,payload TEXT)')
   c.executemany('INSERT INTO messages(contact,sender,time,content) VALUES(?,?,?,?)',[('test','我',f'2026-10-{i//100+1:02d} 12:{i%60:02d}:00',str(i)) for i in range(250)])
  cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler);threading.Thread(target=cls.server.serve_forever,daemon=True).start();cls.base='http://127.0.0.1:'+str(cls.server.server_port)
  cls.cookies=http.cookiejar.CookieJar();cls.client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cls.cookies))
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.tmp.cleanup()
 def request(self,path,body=None,client=None,origin=None):
  headers={'Content-Type':'application/json'}
  if origin:headers['Origin']=origin
  req=urllib.request.Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
  with (client or self.client).open(req) as r:return json.load(r)
 def denied(self,path,body=None,code=401):
  with self.assertRaises(urllib.error.HTTPError) as e:self.request(path,body,urllib.request.build_opener())
  self.assertEqual(e.exception.code,code)
 def test_full_flow(self):
  media_folder=app.ROOT/'data/media';media_folder.mkdir(parents=True)
  name='a'*64;(media_folder/name).write_bytes(b'attachment-test')
  with app.connect() as c:c.execute('INSERT INTO media_assets VALUES(?,?,?,?)',('test-url',name,'image/png',None))
  destination=app.ROOT/'saved.png'
  self.request('/api/save',{'file':name,'destination':str(destination)})
  self.assertEqual(destination.read_bytes(),b'attachment-test')
  with self.assertRaises(urllib.error.HTTPError):self.request('/api/save',{'file':name,'destination':str(destination)})
  self.assertFalse(self.request('/api/auth/status')['enabled'])
  rows=self.request('/api/messages?contact=test')['messages'];self.assertEqual(len(rows),200);self.assertGreaterEqual(rows[0]['time'],rows[-1]['time'])
  first=self.request('/api/messages?contact=test');cursor=first['cursor']
  from urllib.parse import urlencode
  older=self.request('/api/messages?'+urlencode({'contact':'test','before_time':cursor['time'],'before_id':cursor['id']}))
  self.assertEqual(len(older['messages']),50)
  self.assertFalse(older['has_more'])
  self.assertFalse({r['id'] for r in first['messages']} & {r['id'] for r in older['messages']})
  self.assertEqual(len(self.request('/api/messages?contact=test&page=1')['messages']),50)
  self.assertEqual(self.request('/api/messages?contact=test&start=2026-10-03&end=2026-10-03')['total'],50)
  timeline=self.request('/api/timeline?contact=test');self.assertEqual(timeline[0]['day'],'2026-10-03')
  located=self.request('/api/messages?contact=test&at=2026-10-02')
  target=next(r for r in located['messages'] if r['id']==located['target_id'])
  self.assertEqual(target['time'][:10],'2026-10-02')
  self.assertEqual(target['time'],min(r['time'] for r in self.request('/api/messages?contact=test&start=2026-10-02&end=2026-10-02')['messages']))
  self.assertEqual(self.request('/api/messages?contact=test&at=2025-01-01')['target_day'],'2026-10-01')
  with self.assertRaises(urllib.error.HTTPError):self.request('/api/backup/delete',{'contact':'test','password':'anything'})
  self.request('/api/auth/password',{'password':'test-only-secret'})
  self.assertTrue(self.request('/api/auth/status')['enabled'])
  with self.assertRaises(urllib.error.HTTPError):self.request('/api/backup/delete',{'contact':'test','password':'wrong'})
  self.assertEqual(self.request('/api/messages?contact=test')['total'],250)
  self.denied('/api/backup/delete',{'contact':'test','password':'test-only-secret'})
  for route in ['/api/messages?contact=test','/api/contacts','/api/config','/api/timeline','/api/export','/media/abc','/api/ai/settings','/api/ai/messages']:
   self.denied(route)
  self.denied('/api/sync',{'contact':'test'})
  self.denied('/api/add-contact',{'user_id':'12345678'})
  for route in ['/api/ai/send','/api/ai/settings','/api/ai/delete']:self.denied(route,{})
  self.denied('/api/save',{'file':'fake','destination':'/tmp/fake'})
  with self.assertRaises(urllib.error.HTTPError) as e:self.request('/api/auth/password',{'password':'new-secret'},origin='http://evil.example')
  self.assertEqual(e.exception.code,403)
  self.request('/api/auth/lock',{});self.denied('/api/contacts')
  self.request('/api/auth/login',{'password':'test-only-secret'})
  self.assertEqual(len(self.request('/api/contacts')),1)
  with self.assertRaises(urllib.error.HTTPError):self.request('/api/auth/password',{'current':'wrong','password':''})
  self.request('/api/auth/password',{'current':'test-only-secret','password':''})
  self.assertFalse(self.request('/api/auth/status')['enabled'])
  self.assertEqual(len(self.request('/api/contacts',client=urllib.request.build_opener())),1)
if __name__=='__main__':unittest.main()
