from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from fieldway_maps import serve_map
import time,os,secrets,json,hashlib,re,urllib.parse,base64,urllib.request,threading,mimetypes
FILE_LOCK=threading.RLock()
MAP_SEM=threading.BoundedSemaphore(4)
ROOT=Path(__file__).resolve().parent
for folder in ('data','trash'):(ROOT/folder).mkdir(exist_ok=True)
ORIGIN=os.environ.get('FIELDWAY_ORIGIN','http://localhost:8798').rstrip('/')
KEYFILE=ROOT/'access.key'
if not KEYFILE.exists(): KEYFILE.write_text(secrets.token_urlsafe(32))
KEY=KEYFILE.read_text().strip()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def send(self,data,status=200,kind='application/json'):
  if not isinstance(data,bytes):data=json.dumps(data).encode()
  self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.end_headers();self.wfile.write(data)
 def auth(self):return secrets.compare_digest(self.headers.get('X-Field-Key',''),KEY)
 def do_HEAD(self):
  if urllib.parse.urlparse(self.path).path=='/fieldway/maps/region.pmtiles':return serve_map(self,ROOT/'maps/region.pmtiles',head=True)
  return self.send({'error':'Not found'},404)
 def do_GET(self):
  with FILE_LOCK:self.get_locked()
 def get_locked(self):
  path=urllib.parse.urlparse(self.path)
  if path.path=='/fieldway/maps/region.pmtiles':return serve_map(self,ROOT/'maps/region.pmtiles')
  if path.path in ['/fieldway/','/fieldway/index.html']:
   return self.send((ROOT/'public/index.html').read_bytes(),kind='text/html; charset=utf-8')
  if path.path.startswith('/fieldway/vendor/') or path.path in ['/fieldway/offline.html','/fieldway/offline.js','/fieldway/offline-sw.js','/fieldway/manifest.json']:
   name=path.path.removeprefix('/fieldway/')
   if not re.fullmatch(r'[A-Za-z0-9_./-]+',name) or '..' in name:return self.send({'error':'Invalid path'},400)
   p=ROOT/'public'/name
   if not p.is_file():return self.send({'error':'Not found'},404)
   return self.send(p.read_bytes(),kind=mimetypes.guess_type(str(p))[0] or 'application/octet-stream')
  if path.path=='/fieldway/offline-tile':
   if not self.auth():return self.send({'error':'Unauthorized'},401)
   tile=urllib.parse.parse_qs(path.query).get('tile',[''])[0]
   if tile!='latest' and not re.fullmatch(r'[0-9]{8}_[0-9]{6}_pt/(?:[0-9]|1[0-4])/[0-9]{1,5}/[0-9]{1,5}\.pbf',tile):return self.send({'error':'Invalid tile'},400)
   try:
    with MAP_SEM:
     req=urllib.request.Request('https://tiles.openfreemap.org/planet/'+tile,headers={'User-Agent':'FieldWay/1.0 (offline area downloader)'})
     with urllib.request.urlopen(req,timeout=20) as r:
      data=r.read(2000001)
      if len(data)>2000000:raise ValueError('Tile too large')
    return self.send(data,kind='application/json' if tile=='latest' else 'application/x-protobuf')
   except:return self.send({'error':'Map download failed; retry online'},502)
  if path.path=='/fieldway/api/trash':
   if not self.auth():return self.send({'error':'Unauthorized'},401)
   out=[]
   for p in (ROOT/'trash').glob('*.json'):
    try:
     d=json.loads(p.read_text(encoding='utf-8'));out.append({'id':p.stem,'name':d['file']['name'],'trashed':d['trashed']})
    except (OSError,ValueError,KeyError):pass
   return self.send(sorted(out,key=lambda x:x['trashed'],reverse=True))
  if path.path!='/fieldway/api/maps':return self.send({'error':'Not found'},404)
  if not self.auth():return self.send({'error':'Use the private access link on both devices.'},401)
  ident=urllib.parse.parse_qs(path.query).get('id',[''])[0]
  if ident:
   if not re.fullmatch('[a-f0-9]{64}',ident):return self.send({'error':'Invalid ID'},400)
   p=ROOT/'data'/(ident+'.json')
   return self.send(p.read_bytes()) if p.exists() else self.send({'error':'Not found'},404)
  out=[]
  for p in (ROOT/'data').glob('*.json'):
   try:d=json.loads(p.read_text(encoding='utf-8'));out.append({'id':p.stem,'name':d['name'],'saved':p.stat().st_mtime})
   except:pass
  self.send(sorted(out,key=lambda x:x['saved'],reverse=True))
 def do_POST(self):
  with FILE_LOCK:
   try:self.post_locked()
   except OSError:return self.send({'error':'File operation failed. Your recoverable copy is retained; refresh and retry.'},500)
 def post_locked(self):
  path=urllib.parse.urlparse(self.path)
  if path.path in ['/fieldway/api/maps/trash','/fieldway/api/maps/restore']:
   if not self.auth():return self.send({'error':'Unauthorized'},401)
   if self.headers.get('Origin') not in [None,ORIGIN]:return self.send({'error':'Invalid origin'},403)
   ident=urllib.parse.parse_qs(path.query).get('id',[''])[0]
   if not re.fullmatch('[a-f0-9]{64}',ident):return self.send({'error':'Invalid ID'},400)
   trash=ROOT/'trash';trash.mkdir(exist_ok=True)
   if path.path.endswith('/trash'):
    source=ROOT/'data'/(ident+'.json')
    if not source.is_file():return self.send({'error':'File already moved or not found. Refresh files.'},404)
    raw=source.read_bytes()
    try:record=json.loads(raw)
    except ValueError:return self.send({'error':'Unreadable saved file; nothing changed'},409)
    tid=secrets.token_hex(32)
    dest=trash/(tid+'.json')
    envelope={'original_id':ident,'trashed':time.time(),'file':record,'raw':base64.b64encode(raw).decode()}
    with dest.open('x',encoding='utf-8') as f:
     json.dump(envelope,f);f.flush();os.fsync(f.fileno())
    # Confirm the recoverable original bytes before removing its active entry.
    if base64.b64decode(json.loads(dest.read_text(encoding='utf-8'))['raw'])!=raw:raise OSError('Verification failed')
    source.unlink()
    return self.send({'id':tid,'original_id':ident,'name':record['name'],'trashed':True})
   source=trash/(ident+'.json')
   if not source.is_file():return self.send({'error':'Already restored or not found. Refresh files.'},404)
   record=json.loads(source.read_text(encoding='utf-8'));original=record['original_id']
   if not re.fullmatch('[a-f0-9]{64}',original):return self.send({'error':'Invalid saved record'},409)
   dest=ROOT/'data'/(original+'.json')
   if dest.exists():return self.send({'error':'This file is already in Saved files. The Trash copy is retained.'},409)
   if len(list((ROOT/'data').glob('*.json')))>=100:return self.send({'error':'100-file limit reached. Move another file to Trash first.'},409)
   raw=base64.b64decode(record['raw'],validate=True)
   temp=ROOT/'data'/(secrets.token_hex(12)+'.tmp')
   with temp.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
   temp.rename(dest)
   if dest.read_bytes()!=raw:raise OSError('Verification failed')
   source.unlink()
   return self.send({'id':original,'name':record['file']['name'],'restored':True})

  if urllib.parse.urlparse(self.path).path!='/fieldway/api/maps':return self.send({'error':'Not found'},404)
  if not self.auth():return self.send({'error':'Use the private access link on both devices.'},401)
  if self.headers.get('Origin') not in [None,ORIGIN]:return self.send({'error':'Invalid origin'},403)
  try:n=int(self.headers.get('Content-Length','0'))
  except:return self.send({'error':'Invalid length'},400)
  if n<1 or n>7000000:return self.send({'error':'Maximum file size is 5 MB'},413)
  self.connection.settimeout(15)
  try:
   data=json.loads(self.rfile.read(n));name=str(data.get('name','File'))[:160]
   if 'base64' in data:
    content=base64.b64decode(data['base64'],validate=True)
    saved={'name':name,'base64':data['base64']}
   else:
    content=data['xml'].encode();saved={'name':name,'xml':data['xml']}
   if len(content)>5000000:raise ValueError()
  except:return self.send({'error':'Invalid file or larger than 5 MB'},400)
  ident=hashlib.sha256(content).hexdigest();p=ROOT/'data'/(ident+'.json')
  if not p.exists():
   if len(list((ROOT/'data').glob('*.json')))>=100:return self.send({'error':'100-file limit reached'},400)
   temp=ROOT/'data'/(secrets.token_hex(12)+'.tmp');temp.write_text(json.dumps(saved),encoding='utf-8');temp.replace(p)
  self.send({'id':ident,'name':name})
if __name__=='__main__':
 ThreadingHTTPServer(('127.0.0.1',8798),Handler).serve_forever()
