export const criteria=[
 {key:'smoothness',name:'Terrain Smoothness',weight:.25,explanation:'Lower local height variation provides a more even touchdown surface. This demo rates synthetic roughness over the landing footprint, not LRO measurements.'},
 {key:'slope',name:'Slope Suitability',weight:.20,explanation:'Gentler slopes reduce touchdown tilt. This demo uses an illustrative slope penalty. Vehicle-specific allowable slopes have not been supplied.'},
 {key:'rocks',name:'Rock Density Suitability',weight:.15,explanation:'Higher scores mean fewer exposed rocks in the synthetic footprint. Real assessment requires resolved obstacle sizes and landing-gear clearance.'},
 {key:'hazards',name:'Hazard Avoidance',weight:.20,explanation:'Higher synthetic hazard-free coverage improves this score. Unresolved boulders, pits and navigation error would need to be included in a validated assessment.'},
 {key:'edge',name:'Crater Edge Distance',weight:.10,explanation:'Greater clearance from crater walls is favored, up to a reference clearance. Distance is computed from demo offsets and an approximate circular crater boundary.'},
 {key:'stability',name:'Surface Stability',weight:.10,explanation:'This synthetic stability index represents ground consistency. It is not a measurement of regolith strength or a prediction of landing-gear settlement.'}
];
export const craters=[
 {id:'tycho',name:'Tycho Crater',lat:-43.31,lon:-11.36,diameter:85,depth:4.8,region:'SOUTHERN HIGHLANDS',description:'Terraced walls / ray system',shift:0},
 {id:'copernicus',name:'Copernicus Crater',lat:9.62,lon:-20.08,diameter:93,depth:3.8,region:'OCEANUS PROCELLARUM',description:'Terraced walls / central peaks',shift:1},
 {id:'clavius',name:'Clavius Crater',lat:-58.75,lon:-14.4,diameter:225,depth:3.5,region:'SOUTHERN HIGHLANDS',description:'Walled plain / nested impacts',shift:2}
];
const fixtures=[
 {id:'A',x:8,y:3,roughness:.10,slopeDeg:1.4,rockCover:.12,hazardFree:.96,stability:91},
 {id:'B',x:11,y:5,roughness:.16,slopeDeg:1.8,rockCover:.14,hazardFree:.94,stability:90},
 {id:'C',x:9,y:7,roughness:.20,slopeDeg:2.2,rockCover:.16,hazardFree:.92,stability:89},
 {id:'D',x:13,y:8,roughness:.24,slopeDeg:2.6,rockCover:.18,hazardFree:.90,stability:88}
];
export function zonesFor(crater){return fixtures.map((f,i)=>{const x=f.x+crater.shift,y=f.y+crater.shift*.5;return {...f,x,y,lat:crater.lat+y/1737.4*180/Math.PI,lon:crater.lon+x/(1737.4*Math.cos(crater.lat*Math.PI/180))*180/Math.PI,roughness:f.roughness+crater.shift*.015,slopeDeg:f.slopeDeg+crater.shift*.3,edgeKm:crater.diameter/2-Math.hypot(x,y),referenceClearance:35+crater.shift*4,profileSeed:i+crater.shift*5}})}
export const sourceNote='Site measurements, normalized criteria and elevation profiles are synthetic demo data. Crater dimensions and locations are approximate context only. NASA imagery is used for visualization, not as evidence for these scores.';
