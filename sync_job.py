import threading,subprocess,sys,time,json
import contacts
from pathlib import Path
ROOT=Path(__file__).resolve().parent
STATE={'running':False,'stage':'','error':None};LOCK=threading.Lock()
def start(contact=None,user_id=None):
 target=contacts.resolve(user_id) if user_id else contacts.registered(contact)
 with LOCK:
  if STATE['running']:raise ValueError('另一个会话正在备份，请完成后再添加')
  STATE.update(running=True,stage='读取最新本地聊天记录',error=None,contact=target['contact'])
 def worker():
  try:
   for script,stage in [('export_rednote.py','备份并更新聊天记录'),('media.py','下载新增附件')]:
    with LOCK:STATE['stage']=stage
    p=subprocess.run([sys.executable,str(ROOT/script)]+(['--user',target['public_id']] if script=='export_rednote.py' else []),cwd=ROOT,capture_output=True,text=True)
    if p.returncode:raise RuntimeError(stage+'失败，请检查小红书目录权限或网络')
   with LOCK:STATE.update(stage='更新完成',finished=time.time())
  except Exception as e:
   with LOCK:STATE.update(stage='更新失败',error=str(e))
  finally:
   with LOCK:STATE['running']=False
 threading.Thread(target=worker,daemon=True).start();return dict(STATE)
def status():
 with LOCK:return dict(STATE)
