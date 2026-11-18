"""Same-origin immutable PMTiles range serving. No directory listing or user data."""
import re
MAX_RANGE=8*1024*1024
def serve_map(handler,path,head=False):
 if not path.is_file():
  handler.send_error(404);return
 size=path.stat().st_size
 etag='"%x-%x"'%(size,path.stat().st_mtime_ns)
 raw=handler.headers.get('Range')
 if head:
  handler.send_response(200);handler.send_header('Content-Length',str(size))
  handler.send_header('Content-Type','application/vnd.pmtiles');handler.send_header('Accept-Ranges','bytes')
  handler.send_header('ETag',etag);handler.send_header('Cache-Control','public, max-age=86400');handler.end_headers();return
 if not raw:
  handler.send_error(400,'Byte Range required');return
 m=re.fullmatch(r'bytes=(\d*)-(\d*)',raw)
 try:
  if not m or not any(m.groups()):raise ValueError()
  if m[1]:
   start=int(m[1]);end=min(int(m[2]) if m[2] else start+MAX_RANGE-1,size-1)
  else:
   n=int(m[2]);start=max(0,size-n);end=size-1
  if start<0 or start>=size or end<start or end-start+1>MAX_RANGE:raise ValueError()
 except ValueError:
  handler.send_response(416);handler.send_header('Content-Range','bytes */'+str(size));handler.send_header('Content-Length','0');handler.end_headers();return
 if handler.headers.get('If-Match') not in (None,etag,'*'):
  handler.send_response(412);handler.send_header('Content-Length','0');handler.end_headers();return
 handler.send_response(206);handler.send_header('Content-Type','application/vnd.pmtiles')
 handler.send_header('Accept-Ranges','bytes');handler.send_header('Content-Range',f'bytes {start}-{end}/{size}')
 handler.send_header('Content-Length',str(end-start+1));handler.send_header('ETag',etag)
 handler.send_header('Cache-Control','public, max-age=86400');handler.send_header('X-Content-Type-Options','nosniff');handler.end_headers()
 with path.open('rb') as f:
  f.seek(start);remaining=end-start+1
  while remaining:
   chunk=f.read(min(65536,remaining))
   if not chunk:break
   handler.wfile.write(chunk);remaining-=len(chunk)

