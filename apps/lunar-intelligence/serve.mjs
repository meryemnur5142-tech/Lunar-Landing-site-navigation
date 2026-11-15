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
  https.get(target,{headers:{'User-Agent':'LUNA-AI/1.0'}},(hr)=>{
    const chunks=[];
    hr.on('data',c=>chunks.push(c));
    hr.on('end',()=>{
      res.writeHead(200,{'Content-Type':'application/json','Access-Control-Allow-Origin':'*','Cache-Control':'no-cache'});
      res.end(Buffer.concat(chunks));
    });
  }).on('error',e=>{res.writeHead(502);res.end(JSON.stringify({error:e.message}));});
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
