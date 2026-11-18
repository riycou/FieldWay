import importlib.util,json,pathlib,shutil,sys,tempfile,threading,unittest,urllib.request,urllib.error
from http.server import ThreadingHTTPServer
ROOT=pathlib.Path(__file__).resolve().parents[1]
class ApiTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();root=pathlib.Path(cls.tmp.name)
  for name in ('server.py','fieldway_maps.py'):shutil.copyfile(ROOT/name,root/name)
  shutil.copytree(ROOT/'public',root/'public',ignore=shutil.ignore_patterns('vendor'))
  sys.path.insert(0,str(root));spec=importlib.util.spec_from_file_location('fieldway_test_server',root/'server.py');cls.mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.mod)
  cls.http=ThreadingHTTPServer(('127.0.0.1',0),cls.mod.Handler);cls.worker=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.worker.start()
  cls.url='http://127.0.0.1:'+str(cls.http.server_port)
 @classmethod
 def tearDownClass(cls):
  cls.http.shutdown();cls.http.server_close();cls.worker.join();sys.path.pop(0);cls.tmp.cleanup()
 def request(self,path,body=None,authorized=True,origin=None):
  headers={'Content-Type':'application/json'}
  if authorized:headers['X-Field-Key']=self.mod.KEY
  if origin:headers['Origin']=origin
  req=urllib.request.Request(self.url+path,data=None if body is None else json.dumps(body).encode(),headers=headers)
  try:r=urllib.request.urlopen(req)
  except urllib.error.HTTPError as e:r=e
  with r:return r.status,r.read()
 def test_auth_and_files(self):
  self.assertEqual(self.request('/fieldway/api/maps',authorized=False)[0],401)
  body={'name':'Synthetic test','xml':'<kml><Document><name>Test only</name></Document></kml>'}
  self.assertEqual(self.request('/fieldway/api/maps',body,origin='https://invalid.example')[0],403)
  code,raw=self.request('/fieldway/api/maps',body,origin=self.mod.ORIGIN);self.assertEqual(code,200);ident=json.loads(raw)['id']
  self.assertEqual(len(json.loads(self.request('/fieldway/api/maps')[1])),1)
  self.assertEqual(json.loads(self.request('/fieldway/api/maps?id='+ident)[1])['xml'],body['xml'])
  code,raw=self.request('/fieldway/api/maps/trash?id='+ident,{});self.assertEqual(code,200);tid=json.loads(raw)['id']
  self.assertEqual(json.loads(self.request('/fieldway/api/maps')[1]),[])
  self.assertEqual(len(json.loads(self.request('/fieldway/api/trash')[1])),1)
  self.assertEqual(self.request('/fieldway/api/maps/restore?id='+tid,{})[0],200)
  self.assertEqual(json.loads(self.request('/fieldway/api/maps?id='+ident)[1])['xml'],body['xml'])
 def test_static_and_bad_paths(self):
  self.assertEqual(self.request('/fieldway/')[0],200)
  self.assertEqual(self.request('/fieldway/vendor/../access.key')[0],400)
  self.assertEqual(self.request('/fieldway/access.key')[0],404)
  self.assertEqual(self.request('/fieldway/maps/region.pmtiles')[0],404)
  self.assertEqual(self.request('/fieldway/api/maps?id=invalid')[0],400)
if __name__=='__main__':unittest.main()
