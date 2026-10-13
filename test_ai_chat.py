import tempfile,sqlite3,time,json,threading
from pathlib import Path
import ai_chat
with tempfile.TemporaryDirectory() as folder:
 root=Path(folder);ai_chat.DB=root/'ai.db';ai_chat.CONFIG=root/'config.json';real=root/'real.db'
 c=sqlite3.connect(real);c.execute('CREATE TABLE messages(contact TEXT,sender TEXT,content TEXT,time TEXT,id INTEGER)')
 c.executemany('INSERT INTO messages VALUES(?,?,?,?,?)',[('A','A','你好呀～','2026-01-01',1),('B','B','other-person-secret','2026-01-02',2)]);c.commit();c.close();original=real.read_bytes()
 assert ai_chat.public_settings()['days']==1
 for days in (1,7,30,60,0):
  ai_chat.configure({'days':days,'key':'test-key','model':'test-model'})
  with ai_chat.connect() as c:
   c.execute('DELETE FROM messages')
   c.execute('INSERT INTO messages(contact,role,content,created) VALUES(?,?,?,?)',('A','user','old',time.time()-70*86400))
  ai_chat.cleanup();assert len(ai_chat.history('A'))==(1 if days==0 else 0)
 ai_chat.configure({'days':1})
 import io
 from unittest.mock import patch
 class Response(io.BytesIO):
  def __enter__(self):return self
  def __exit__(self,*args):self.close()
 def mock_http(req,timeout):
  assert req.full_url=='https://api.openai.com/v1/responses'
  payload=json.loads(req.data);assert payload['store'] is False
  assert payload['model']=='test-model'
  return Response(json.dumps({'output':[{'content':[{'type':'output_text','text':'模拟接口回复'}]}]}).encode())
 with patch('ai_chat.urllib.request.urlopen',mock_http):
  assert ai_chat.call_model([{'role':'user','content':'test'}],[{'sender':'A','text':'test'}],'A')=='模拟接口回复'
 seen=[]
 def mock(messages,examples,contact):
  assert contact=='A';assert all('other-person-secret' not in e['text'] for e in examples['examples'])
  seen.append(messages);return '你好呀～（测试模拟）'
 ai_chat.call_model=mock
 rows=ai_chat.send(real,'A','你好');assert len(rows)==2 and all(r['ai'] for r in rows)
 assert real.read_bytes()==original
 ai_chat.delete('A');assert not ai_chat.history('A')
 entered=threading.Event();resume=threading.Event();errors=[]
 def slow(*args):entered.set();resume.wait(5);return 'test'
 ai_chat.call_model=slow
 def worker():
  try:ai_chat.send(real,'A','pending')
  except ValueError as e:errors.append(str(e))
 thread=threading.Thread(target=worker);thread.start();assert entered.wait(5);ai_chat.delete('A');resume.set();thread.join(5)
 assert errors and not ai_chat.history('A')
 assert real.read_bytes()==original
 ai_chat.MODEL_TIMEOUT=.05
 def stalled(*args):time.sleep(.2);return 'late reply'
 ai_chat.call_model=stalled
 try:ai_chat.send(real,'A','timeout')
 except ValueError as e:assert '45' in str(e)
 else:raise AssertionError('request should time out')
 assert 'A' not in ai_chat.BUSY and not ai_chat.history('A')
 time.sleep(.25);assert not ai_chat.history('A')
 print('PASS: separate storage, all retention options, contact isolation, deletion, and no resurrection after in-flight delete')
