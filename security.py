import hashlib,hmac,json,secrets,time,threading
from pathlib import Path
FILE=Path(__file__).resolve().parent/'data/security.json'
SESSIONS={};ATTEMPTS={};LOCK=threading.RLock()
def config():
 return json.loads(FILE.read_text()) if FILE.exists() else {}
def enabled():return bool(config().get('hash'))
def check(password):
 d=config()
 if not d:return False
 digest=hashlib.scrypt(password.encode(),salt=bytes.fromhex(d['salt']),n=16384,r=8,p=1).hex()
 return hmac.compare_digest(digest,d['hash'])
def authenticated(token):
 with LOCK:return not enabled() or SESSIONS.get(token,0)>time.time()
def session():
 token=secrets.token_urlsafe(32)
 with LOCK:SESSIONS[token]=time.time()+8*3600
 return token
def set_password(password):
 if password and len(password)<6:raise ValueError('密码至少6位')
 with LOCK:
  if password:
   salt=secrets.token_bytes(16)
   d={'salt':salt.hex(),'hash':hashlib.scrypt(password.encode(),salt=salt,n=16384,r=8,p=1).hex()}
   temp=FILE.with_suffix('.tmp');temp.write_text(json.dumps(d));temp.chmod(0o600);temp.replace(FILE)
  elif FILE.exists():FILE.unlink()
  SESSIONS.clear()
def login(password,address):
 now=time.time()
 with LOCK:
  failures,until=ATTEMPTS.get(address,(0,0))
  if until>now:raise ValueError('尝试过于频繁，请一分钟后再试')
  if not check(password):
   failures+=1;ATTEMPTS[address]=(failures,now+60 if failures>=5 else 0)
   raise ValueError('密码不正确')
  ATTEMPTS.pop(address,None);return session()
