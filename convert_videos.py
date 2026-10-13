import sqlite3,subprocess
from pathlib import Path
c=sqlite3.connect('data/chats.sqlite3',timeout=30)
rows=c.execute("SELECT url,path FROM media_assets WHERE mime='video/mp4' AND path IS NOT NULL AND path NOT LIKE '%.mp4'").fetchall()
for url,name in rows:
 path=Path('data/media')/name;out=path.with_name(name+'.mp4')
 result=subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-i',str(path),'-c:v','libx264','-threads','2','-preset','fast','-crf','22','-c:a','aac','-movflags','+faststart',str(out)],capture_output=True,timeout=300)
 if result.returncode:print('视频转换失败',flush=True);continue
 c.execute('UPDATE media_assets SET path=? WHERE url=?',(out.name,url));c.commit();print('已转换视频',flush=True)
