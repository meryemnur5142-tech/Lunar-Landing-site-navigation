import {craters,zonesFor,criteria,vehicles} from './data.js';
import {rankZones} from './scoring.js';
import {$,CraterInformation,LandingZoneList,ClusterMap,LandingAnalysis,TerrainProfile,CriterionModal,DetailedAnalysisModal,MethodologyModal,VehiclePanel} from './components.js';
import {MoonVisualization} from './moon.js';
let crater=craters[0],zones=rankZones(zonesFor(crater)),selected='A',moon,selectedVehicle=vehicles[0].id;
const current=()=>zones.find(z=>z.id===selected);
function selectZone(id,details=false){selected=id;render();moon?.select(id);if(details)DetailedAnalysisModal(current(),zones,crater)}
function render(){const veh=vehicles.find(v=>v.id===selectedVehicle)||vehicles[0];CraterInformation(crater,zones);LandingZoneList(zones,selected,selectZone);ClusterMap(zones,selected,selectZone);LandingAnalysis(current(),key=>CriterionModal(current(),key),veh);TerrainProfile(current());VehiclePanel(selectedVehicle,id=>{selectedVehicle=id;render();});}
$('craterSelect').innerHTML=craters.map(c=>`<option value="${c.id}">${c.name}</option>`).join('');
$('craterSelect').onchange=()=>{crater=craters.find(c=>c.id===$('craterSelect').value);zones=rankZones(zonesFor(crater));selected=zones[0].id;render();moon?.setCrater(crater,zones);$('analysisStatus').textContent=`${crater.name}: 2 verimli + 2 riskli bölge değerlendirildi.`};
render();
try{moon=new MoonVisualization($('moonCanvas'),crater,zones,selectZone)}catch(e){console.error(e);$('sceneLoading').hidden=true;$('sceneError').hidden=false;['orbitButton','approachButton','rotateButton','zoomIn','zoomOut','resetView'].forEach(id=>$(id).disabled=true)}
$('orbitButton').onclick=()=>moon?.orbit();$('approachButton').onclick=()=>moon?.approach();$('rotateButton').onclick=()=>moon?.toggleRotation();$('zoomIn').onclick=()=>moon?.zoom(.8);$('zoomOut').onclick=()=>moon?.zoom(1.25);$('resetView').onclick=()=>moon?.reset();
$('scoreButton').onclick=$('detailsButton').onclick=()=>DetailedAnalysisModal(current(),zones,crater);
$('methodButton').onclick=$('weightsButton').onclick=MethodologyModal;
document.querySelector('.modal-close').onclick=()=>$('analysisModal').close();
$('analysisModal').addEventListener('click',e=>{if(e.target===$('analysisModal')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close()}});
$('rescanButton').onclick=()=>{const button=$('rescanButton');button.disabled=true;$('analysisStatus').textContent='Altı kriter 4 bölge üzerinden değerlendiriliyor (2 verimli + 2 riskli)…';document.querySelector('.moon-panel').classList.add('scanning');setTimeout(()=>{zones=rankZones(zonesFor(crater));render();document.querySelector('.moon-panel').classList.remove('scanning');button.disabled=false;$('analysisStatus').textContent='Analiz tamamlandı. Aynı girdiler aynı skorları üretir.'},1400)};
function tick(){$('clock').textContent=new Date().toISOString().replace('T',' / ').slice(0,21)+' UTC'}tick();setInterval(tick,1000);
const _origWeights=criteria.map(c=>c.weight);
function buildWeightEditor(){
  $('weightRows').innerHTML=criteria.map((c,i)=>`<div class="wrow"><span class="wlabel">${c.name.split(' ').slice(0,2).join(' ').toUpperCase()}</span><input class="wslider" type="range" min="0" max="50" step="1" value="${Math.round(c.weight*100)}" data-idx="${i}"><span class="wval" id="wv${i}">${Math.round(c.weight*100)}%</span></div>`).join('');
  document.querySelectorAll('.wslider').forEach(sl=>{
    sl.oninput=()=>{
      const vals=[...document.querySelectorAll('.wslider')].map(s=>+s.value);
      const sum=vals.reduce((a,b)=>a+b,0)||1;
      criteria.forEach((c,i)=>{c.weight=vals[i]/sum;$('wv'+i).textContent=Math.round(c.weight*100)+'%'});
      $('weightTotal').textContent='TOTAL INPUT: '+Math.round(vals.reduce((a,b)=>a+b,0))+'%';
      zones=rankZones(zonesFor(crater));render();
    };
  });
}
buildWeightEditor();
$('resetWeights').onclick=()=>{
  criteria.forEach((c,i)=>{c.weight=_origWeights[i]});
  document.querySelectorAll('.wslider').forEach((sl,i)=>{sl.value=Math.round(_origWeights[i]*100);$('wv'+i).textContent=Math.round(_origWeights[i]*100)+'%'});
  $('weightTotal').textContent='TOTAL INPUT: 100%';
  zones=rankZones(zonesFor(crater));render();
};
