import {craters,zonesFor} from './data.js';
import {rankZones} from './scoring.js';
import {$,CraterInformation,LandingZoneList,ClusterMap,LandingAnalysis,TerrainProfile,CriterionModal,DetailedAnalysisModal,MethodologyModal} from './components.js';
import {MoonVisualization} from './moon.js';
let crater=craters[0],zones=rankZones(zonesFor(crater)),selected='A',moon;
const current=()=>zones.find(z=>z.id===selected);
function selectZone(id,details=false){selected=id;render();moon?.select(id);if(details)DetailedAnalysisModal(current(),zones,crater)}
function render(){CraterInformation(crater,zones);LandingZoneList(zones,selected,selectZone);ClusterMap(zones,selected,selectZone);LandingAnalysis(current(),key=>CriterionModal(current(),key));TerrainProfile(current())}
$('craterSelect').innerHTML=craters.map(c=>`<option value="${c.id}">${c.name}</option>`).join('');
$('craterSelect').onchange=()=>{crater=craters.find(c=>c.id===$('craterSelect').value);zones=rankZones(zonesFor(crater));selected=zones[0].id;render();moon?.setCrater(crater,zones);$('analysisStatus').textContent=`${crater.name}: four demo sites evaluated.`};
render();
try{moon=new MoonVisualization($('moonCanvas'),crater,zones,selectZone)}catch(e){console.error(e);$('sceneLoading').hidden=true;$('sceneError').hidden=false;['orbitButton','approachButton','rotateButton','zoomIn','zoomOut','resetView'].forEach(id=>$(id).disabled=true)}
$('orbitButton').onclick=()=>moon?.orbit();$('approachButton').onclick=()=>moon?.approach();$('rotateButton').onclick=()=>moon?.toggleRotation();$('zoomIn').onclick=()=>moon?.zoom(.8);$('zoomOut').onclick=()=>moon?.zoom(1.25);$('resetView').onclick=()=>moon?.reset();
$('scoreButton').onclick=$('detailsButton').onclick=()=>DetailedAnalysisModal(current(),zones,crater);
$('methodButton').onclick=$('weightsButton').onclick=MethodologyModal;
document.querySelector('.modal-close').onclick=()=>$('analysisModal').close();
$('analysisModal').addEventListener('click',e=>{if(e.target===$('analysisModal')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close()}});
$('rescanButton').onclick=()=>{const button=$('rescanButton');button.disabled=true;$('analysisStatus').textContent='Evaluating six criteria across four sites…';document.querySelector('.moon-panel').classList.add('scanning');setTimeout(()=>{zones=rankZones(zonesFor(crater));render();document.querySelector('.moon-panel').classList.remove('scanning');button.disabled=false;$('analysisStatus').textContent='Analysis complete. Same inputs produce the same scores.'},1400)};
function tick(){$('clock').textContent=new Date().toISOString().replace('T',' / ').slice(0,21)+' UTC'}tick();setInterval(tick,1000);
