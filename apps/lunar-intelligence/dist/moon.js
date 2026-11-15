import * as THREE from './vendor/three.js';
import {$} from './components.js';
const radius=2.2;
const location=(lat,lon,r=radius)=>{const a=lat*Math.PI/180,b=lon*Math.PI/180;return new THREE.Vector3(r*Math.cos(a)*Math.cos(b),r*Math.sin(a),-r*Math.cos(a)*Math.sin(b))};
export class MoonVisualization{
 constructor(container,crater,zones,onSelect){
  this.container=container;this.crater=crater;this.zones=zones;this.onSelect=onSelect;this.selected='A';this.mode='orbit';this.rotating=!matchMedia('(prefers-reduced-motion: reduce)').matches;this.offset=0;this.distance=8.3;this.currentTarget=new THREE.Vector3();this.target=new THREE.Vector3();this.desiredPosition=new THREE.Vector3(0,.1,this.distance);
  this.renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});this.renderer.setPixelRatio(Math.min(devicePixelRatio,2));this.renderer.outputColorSpace=THREE.SRGBColorSpace;this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.3;container.appendChild(this.renderer.domElement);
  this.scene=new THREE.Scene();this.camera=new THREE.PerspectiveCamera(38,1,.001,100);this.camera.position.copy(this.desiredPosition);
  this.scene.add(new THREE.AmbientLight(0xd6e3f0,.32));this.sun=new THREE.DirectionalLight(0xfff7eb,2.8);this.sun.position.set(-3,3,7);this.scene.add(this.sun);
  this.globe=new THREE.Group();this.globe.rotation.y=-Math.PI/2;this.scene.add(this.globe);
  const manager=new THREE.LoadingManager(()=>{$('sceneLoading').hidden=true;this.renderer.domElement.dataset.loaded='true'});manager.onError=()=>{$('sceneLoading').hidden=true;$('sceneError').hidden=false;$('sceneError').textContent='Lunar texture could not load. Analysis data is still available.'};
  const loader=new THREE.TextureLoader(manager),texture=loader.load('assets/moon-color.jpg'),height=loader.load('assets/moon-height.jpg');texture.colorSpace=THREE.SRGBColorSpace;texture.anisotropy=Math.min(8,this.renderer.capabilities.getMaxAnisotropy());
  this.moon=new THREE.Mesh(new THREE.SphereGeometry(radius,192,128),new THREE.MeshStandardMaterial({map:texture,bumpMap:height,bumpScale:.012,roughness:1,metalness:0}));this.globe.add(this.moon);
  // 130-km north-up LROC Tycho mosaic, draped approximately for visual context.
  // The image already contains real illumination; do not light it a second time.
  const detailTexture=loader.load('assets/tycho-detail.png');detailTexture.colorSpace=THREE.SRGBColorSpace;detailTexture.anisotropy=8;
  const patch=new THREE.PlaneGeometry(130/1737.4*radius,130/1737.4*radius,48,48);
  const normal=location(-43.31,-11.36,1),longitude=-11.36*Math.PI/180,east=new THREE.Vector3(-Math.sin(longitude),0,-Math.cos(longitude)),north=new THREE.Vector3().crossVectors(normal,east).normalize();
  const p=patch.attributes.position;for(let i=0;i<p.count;i++){const v=normal.clone().multiplyScalar(radius).addScaledVector(east,p.getX(i)).addScaledVector(north,p.getY(i)).normalize().multiplyScalar(radius+.0006);p.setXYZ(i,v.x,v.y,v.z)}patch.computeVertexNormals();
  this.detailPatch=new THREE.Mesh(patch,new THREE.MeshBasicMaterial({map:detailTexture,toneMapped:false}));this.detailPatch.visible=false;this.globe.add(this.detailPatch);
  // A subtle navigation orbit, not an atmospheric shell around the Moon.
  const orbit=new THREE.Mesh(new THREE.TorusGeometry(2.75,.002,4,220),new THREE.MeshBasicMaterial({color:0x195a7c,transparent:true,opacity:.4}));orbit.rotation.set(1.13,.2,-.1);this.scene.add(orbit);this.orbitRing=orbit;
  let seed=42;const rand=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296};const vertices=[];for(let i=0;i<650;i++)vertices.push((rand()-.5)*40,(rand()-.5)*30,-12-rand()*15);const stars=new THREE.BufferGeometry();stars.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));this.scene.add(new THREE.Points(stars,new THREE.PointsMaterial({color:0x89c1df,size:.015,transparent:true,opacity:.65})));
  this.markers=new THREE.Group();this.globe.add(this.markers);this.setCrater(crater,zones,false);
  this.resizeObserver=new ResizeObserver(()=>{const {width,height}=container.getBoundingClientRect();this.renderer.setSize(width,height);this.camera.aspect=width/height;this.camera.updateProjectionMatrix()});this.resizeObserver.observe(container);
  let drag=null;const canvas=this.renderer.domElement;
  canvas.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId)});
  canvas.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;drag={x:e.clientX,y:e.clientY};this.rotating=false;this.syncButtons();if(this.mode==='orbit'){this.globe.rotation.y+=dx*.004;this.globe.rotation.x=THREE.MathUtils.clamp(this.globe.rotation.x+dy*.003,-.6,.6)}else{this.offset=THREE.MathUtils.clamp(this.offset+dx*.008,-1.1,1.1);this.focus()}});
  canvas.addEventListener('pointerup',()=>drag=null);canvas.addEventListener('pointercancel',()=>drag=null);
  canvas.addEventListener('wheel',e=>{e.preventDefault();this.zoom(e.deltaY>0?1.08:.92)},{passive:false});
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();$('sceneError').hidden=false;$('sceneError').textContent='Graphics context lost. Reload to restore the 3D view.'});
  this.last=performance.now();this.syncButtons();this.frame=this.frame.bind(this);requestAnimationFrame(this.frame);
 }
 setCrater(crater,zones,reset=true){
  this.crater=crater;this.zones=zones;this.selected=zones[0].id;
  while(this.markers.children.length){const m=this.markers.children[0];m.geometry.dispose();m.material.dispose();this.markers.remove(m)}
  const size=crater.diameter/1737.4*radius/2;const ring=new THREE.Mesh(new THREE.RingGeometry(size*.995,size,96),new THREE.MeshBasicMaterial({color:0x37d5ff,transparent:true,opacity:.5,side:THREE.DoubleSide,depthWrite:false}));const center=location(crater.lat,crater.lon,radius+.002);ring.position.copy(center);ring.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1),center.clone().normalize());this.markers.add(ring);
  $('moonLabels').innerHTML=`<button class="moon-marker crater-marker" aria-label="Approach ${crater.name}"><span>⌖</span><div>${crater.name.toUpperCase()}<small>4 CANDIDATES / APPROACH ↗</small></div></button>`+zones.map(z=>`<button class="moon-marker zone-marker ${z.id===this.selected?'selected':''}" data-zone="${z.id}" aria-label="Zone ${z.id}: ${z.total.toFixed(1)} out of 100"><span>${z.id}</span><div>ZONE ${z.id} · ${z.total.toFixed(1)}<small>SLOPE ${z.slopeDeg.toFixed(1)}° · CLICK FOR ANALYSIS</small></div></button>`).join('');
  $('moonLabels').querySelector('.crater-marker').onclick=()=>this.approach();$('moonLabels').querySelectorAll('[data-zone]').forEach(b=>b.onclick=()=>this.onSelect(b.dataset.zone,true));
  if(reset){this.globe.rotation.set(0,-Math.PI/2,0);this.offset=0;if(this.mode==='surface')this.focus()}
 }
 select(id){this.selected=id;$('moonLabels').querySelectorAll('[data-zone]').forEach(b=>b.classList.toggle('selected',b.dataset.zone===id))}
 syncButtons(){$('orbitButton').classList.toggle('active',this.mode==='orbit');$('approachButton').classList.toggle('active',this.mode==='surface');$('rotateButton').setAttribute('aria-pressed',String(this.rotating));$('rotateButton').setAttribute('aria-label',this.rotating?'Pause rotation':'Start rotation');$('rotateButton').textContent=this.rotating?'Ⅱ':'▷';$('rotateButton').disabled=this.mode==='surface'}
 orbit(){this.mode='orbit';document.body.dataset.view='orbit';this.sun.position.set(-3,3,7);this.distance=8.3;this.target.set(0,0,0);this.desiredPosition.set(0,.1,this.distance);this.orbitRing.visible=true;this.syncButtons()}
 approach(){this.mode='surface';document.body.dataset.view='surface';this.rotating=false;this.distance=.24;this.offset=0;this.globe.updateMatrixWorld(true);this.focus();this.orbitRing.visible=false;this.syncButtons()}
 focus(){const center=location(this.crater.lat,this.crater.lon).applyMatrix4(this.globe.matrixWorld);this.target.copy(center);const normal=center.clone().normalize(),tangent=new THREE.Vector3().crossVectors(new THREE.Vector3(0,1,0),normal).normalize();this.desiredPosition.copy(center).addScaledVector(normal,this.distance).addScaledVector(tangent,this.offset*this.distance);this.sun.position.copy(center.clone().addScaledVector(normal,6).add(new THREE.Vector3(-2,3,0)))}
 toggleRotation(){if(this.mode==='surface')return;this.rotating=!this.rotating;this.syncButtons()}
 zoom(factor){this.distance=THREE.MathUtils.clamp(this.distance*factor,this.mode==='orbit'?5.2:.045,this.mode==='orbit'?12:.5);if(this.mode==='orbit')this.desiredPosition.set(0,.1,this.distance);else this.focus()}
 reset(){this.globe.rotation.set(0,-Math.PI/2,0);this.rotating=false;this.sun.position.set(-3,3,7);this.orbit()}
 frame(now){requestAnimationFrame(this.frame);const dt=Math.min((now-this.last)/1000,.05);this.last=now;
  if(this.mode==='orbit'&&this.rotating)this.globe.rotation.y+=dt*.012;
  const speed=1-Math.exp(-dt*2.5);this.camera.position.lerp(this.desiredPosition,speed);this.currentTarget.lerp(this.target,speed);this.camera.lookAt(this.currentTarget);this.camera.updateMatrixWorld();this.globe.updateMatrixWorld(true);
  const labels=$('moonLabels');labels.querySelectorAll('button').forEach(b=>{const zone=b.dataset.zone?this.zones.find(z=>z.id===b.dataset.zone):this.crater;const world=location(zone.lat,zone.lon,radius+.0004).applyMatrix4(this.globe.matrixWorld),point=world.clone().project(this.camera);const front=world.clone().normalize().dot(this.camera.position.clone().sub(world).normalize())>0;const correctMode=b.dataset.zone?this.mode==='surface':this.mode==='orbit';b.hidden=!front||!correctMode||point.z>1||Math.abs(point.x)>1||Math.abs(point.y)>1;b.style.left=`${(point.x+1)*50}%`;b.style.top=`${(1-point.y)*50}%`});
  this.detailPatch.visible=this.mode==='surface'&&this.crater.id==='tycho'&&this.camera.position.distanceTo(this.target)<1;
  this.renderer.render(this.scene,this.camera);
 }
}
