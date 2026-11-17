#!/usr/bin/env python3
"""Local UI development bridge. Not production hardened; localhost only by default."""
from __future__ import annotations
import json,mimetypes,pathlib,sys
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse,unquote
from run_integration import assemble,HERE
OUT=HERE/'generated'
class Handler(BaseHTTPRequestHandler):
    def _reply(self,status,body,ctype='application/json; charset=utf-8'):
        data=body if isinstance(body,bytes) else body.encode('utf8')
        self.send_response(status);self.send_header('Content-Type',ctype)
        self.send_header('Access-Control-Allow-Origin','http://localhost:5173')
        self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def _json(self,status,obj):self._reply(status,json.dumps(obj,ensure_ascii=False))
    def do_OPTIONS(self):self._reply(204,b'')
    def do_GET(self):
        url=unquote(urlparse(self.path).path)
        if url=='/api/status':
            conf=json.loads((HERE/'config'/'mission_inputs.json').read_text(encoding='utf8'))
            manifest=json.loads((HERE/'data-platform/inputs/planetary/data_manifest.json').read_text(encoding='utf8'))
            self._json(200,{'status':conf['status'],'reference_region':conf['region'],'layers':[{'id':l['id'],'name':l['name'],'valid_real_data':l['valid_real_data']} for l in manifest['layers']]});return
        if url=='/api/result':
            p=OUT/'luna_frontend.json'
            self._reply(200,p.read_bytes()) if p.exists() else self._json(404,{'error':'Analiz yapılmadı.'});return
        if url.startswith('/assets/'):
            rel=url[len('/assets/'):];p=(OUT/rel).resolve()
            if p.is_file() and p.suffix.lower()=='.png' and OUT.resolve() in p.parents:
                self._reply(200,p.read_bytes(),'image/png');return
        self._json(404,{'error':'Not found'})
    def do_POST(self):
        if urlparse(self.path).path!='/api/analyze':self._json(404,{'error':'Not found'});return
        try:
            n=int(self.headers.get('Content-Length','0'))
            if not 1<=n<=65536:raise ValueError('Invalid content length')
            data=json.loads(self.rfile.read(n));
            if not isinstance(data,dict):raise ValueError('Expected object')
            mode=data.get('mode','demo')
            if mode not in ('demo','real'):raise ValueError('Invalid mode')
            obj=assemble(mode, data.get('utc'))
            self._json(200,obj)
        except (ValueError,RuntimeError) as e:self._json(422,{'error':str(e)})
        except Exception as e:self._json(500,{'error':f'{type(e).__name__}: {e}'})
if __name__=='__main__':
    host='127.0.0.1';port=int(sys.argv[1]) if len(sys.argv)>1 else 8765
    print(f'LUNA-AI local development server at http://{host}:{port} (not public/production)')
    ThreadingHTTPServer((host,port),Handler).serve_forever()
