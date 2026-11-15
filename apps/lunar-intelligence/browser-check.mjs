import {spawn} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const output=path.resolve('outputs');fs.mkdirSync(output,{recursive:true});
const browser=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run','--no-default-browser-check','--disable-gpu-sandbox','--enable-unsafe-swiftshader','--remote-debugging-port=9334',`--user-data-dir=${path.join(output,'edge-profile-2')}`,'about:blank'],{windowsHide:true,stdio:'ignore'});
let socket;const wait=ms=>new Promise(r=>setTimeout(r,ms));
try{
 let tabs;for(let i=0;i<60;i++){try{tabs=await(await fetch('http://127.0.0.1:9334/json')).json();break}catch{await wait(250)}}if(!tabs)throw new Error('Headless browser did not start');
 socket=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j});let id=0;const calls=new Map(),errors=[];
 socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const c=calls.get(m.id);calls.delete(m.id);m.error?c.reject(m.error):c.resolve(m.result)}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails)};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const call=++id;calls.set(call,{resolve,reject});socket.send(JSON.stringify({id:call,method,params}))});
 const run=async expression=>{const result=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(result.exceptionDetails)throw new Error(JSON.stringify(result.exceptionDetails));return result.result.value};
 await send('Runtime.enable');await send('Page.enable');await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1050,deviceScaleFactor:1,mobile:false});await send('Page.navigate',{url:'http://127.0.0.1:5173'});
 for(let i=0;i<60;i++){if(await run("!!document.querySelector('canvas[data-loaded]')"))break;await wait(250)}await wait(1500);
 assert.equal(await run("document.querySelectorAll('.zone-row').length"),4);assert.equal(await run("document.querySelector('#sceneError').hidden"),true);assert.equal(await run("!!document.querySelector('canvas[data-loaded]')"),true);
 const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});fs.writeFileSync(path.join(output,'dashboard.png'),Buffer.from(shot.data,'base64'));
 const score=await run("document.querySelector('#scoreValue').textContent");const profile=await run("document.querySelector('#terrainChart').innerHTML");
 await run("document.querySelector('.zone-row[data-zone=B]').click()");assert.equal(await run("document.querySelector('#analysisModal').open"),true);assert.notEqual(await run("document.querySelector('#scoreValue').textContent"),score);assert.notEqual(await run("document.querySelector('#terrainChart').innerHTML"),profile);
 await run("document.querySelector('.modal-close').click();document.querySelector('[data-criterion=slope]').click()");assert.match(await run("document.querySelector('#modalContent').textContent"),/Slope|SLOPE/);
 await run("document.querySelector('.modal-close').click();document.querySelector('#approachButton').click()");await wait(4000);assert.equal(await run("document.querySelectorAll('.zone-marker:not([hidden])').length"),4);
 const surface=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(output,'surface.png'),Buffer.from(surface.data,'base64'));
 await run("document.querySelector('#craterSelect').value='copernicus';document.querySelector('#craterSelect').dispatchEvent(new Event('change'))");assert.match(await run("document.querySelector('#sceneTitle').textContent"),/Copernicus/);
 await run("document.querySelector('#rescanButton').click()");assert.equal(await run("document.querySelector('#rescanButton').disabled"),true);await wait(1700);assert.equal(await run("document.querySelector('#rescanButton').disabled"),false);
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await run("document.querySelector('#resetView').click()");await wait(2500);assert.ok(await run("document.documentElement.scrollWidth<=innerWidth+1"));const mobile=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(output,'mobile.png'),Buffer.from(mobile.data,'base64'));
 assert.deepEqual(errors,[]);console.log('PASS: real WebGL/textures, 4 zones, synchronized score/profile, details, criterion dialog, approach markers, crater switch, re-analysis, mobile overflow, no runtime exceptions.');
 await send('Browser.close');
}finally{socket?.close();browser.kill()}
