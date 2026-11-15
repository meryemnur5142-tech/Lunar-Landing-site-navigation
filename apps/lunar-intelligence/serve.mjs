import http from 'node:http';
import https from 'node:https';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('./dist/',import.meta.url));
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.jpg':'image/jpeg','.png':'image/png','.svg':'image/svg+xml'};

function horizonsProxy(req,res){
  const qs=new URL(req.url,'http://localhost').search;
  const target='https://ssd-api.jpl.nasa.gov/horizons.api'+qs;
  const hdrs={'Content-Type':'application/json','Access-Control-Allow-Origin':'*','Cache-Control':'no-cache'};
  https.get(target,{headers:{'User-Agent':'LUNA-AI/1.0'}},(hr)=>{
    const chunks=[];
    hr.on('data',c=>chunks.push(c));
    hr.on('end',()=>{
      const body=Buffer.concat(chunks).toString('utf8');
      res.writeHead(200,hdrs);
      // Wrap non-JSON responses (HTML error pages) so the browser gets a clean error message
      try{JSON.parse(body);res.end(body);}
      catch{res.end(JSON.stringify({error:`NASA Horizons HTML yanıtı (${hr.statusCode}): ${body.slice(0,300)}`}));}
    });
  }).on('error',e=>{res.writeHead(200,hdrs);res.end(JSON.stringify({error:`NASA bağlantı hatası: ${e.message}`}));});
}

http.createServer((req,res)=>{
  try{
    const url=new URL(req.url,'http://localhost');
    if(url.pathname==='/horizons-proxy'){horizonsProxy(req,res);return;}
    const pathname=decodeURIComponent(url.pathname),target=path.resolve(root,'.'+(pathname==='/'?'/index.html':pathname));
    if(!target.startsWith(root)||!fs.existsSync(target)||!fs.statSync(target).isFile()){res.writeHead(404);res.end('Not found');return;}
    res.writeHead(200,{'Content-Type':mime[path.extname(target)]||'application/octet-stream','Cache-Control':'no-cache'});
    fs.createReadStream(target).pipe(res);
  }catch{res.writeHead(400);res.end('Bad request');}
}).listen(5173,'127.0.0.1',()=>console.log('Local: http://127.0.0.1:5173'));
