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
 {id:'clavius',name:'Clavius Crater',lat:-58.75,lon:-14.4,diameter:225,depth:3.5,region:'SOUTHERN HIGHLANDS',description:'Walled plain / nested impacts',shift:2},
 {id:'mons-mouton',name:'Mons Mouton',lat:-83.9,lon:-3.9,diameter:97,depth:1.8,region:'SOUTH POLAR HIGHLAND',description:'Polar massif — IM-2 landing site (Mar 2025)',shift:3},
];
const fixtures=[
 {id:'A',x:8, y:3, roughness:.08,slopeDeg:1.1,rockCover:.09,hazardFree:.97,stability:94},
 {id:'B',x:11,y:5, roughness:.13,slopeDeg:1.6,rockCover:.12,hazardFree:.95,stability:91},
 {id:'C',x:7, y:6, roughness:.18,slopeDeg:2.3,rockCover:.17,hazardFree:.90,stability:87},
 {id:'D',x:14,y:4, roughness:.22,slopeDeg:3.0,rockCover:.20,hazardFree:.87,stability:84},
 {id:'E',x:10,y:9, roughness:.27,slopeDeg:3.8,rockCover:.24,hazardFree:.82,stability:79},
 {id:'F',x:6, y:10,roughness:.34,slopeDeg:5.1,rockCover:.30,hazardFree:.73,stability:70},
 {id:'G',x:15,y:11,roughness:.42,slopeDeg:6.8,rockCover:.38,hazardFree:.62,stability:58},
];
export function zonesFor(crater){return fixtures.map((f,i)=>{const x=f.x+crater.shift,y=f.y+crater.shift*.5;return {...f,x,y,lat:crater.lat+y/1737.4*180/Math.PI,lon:crater.lon+x/(1737.4*Math.cos(crater.lat*Math.PI/180))*180/Math.PI,roughness:f.roughness+crater.shift*.015,slopeDeg:f.slopeDeg+crater.shift*.3,edgeKm:crater.diameter/2-Math.hypot(x,y),referenceClearance:35+crater.shift*4,profileSeed:i+crater.shift*5}})}
export const sourceNote='Site measurements, normalized criteria and elevation profiles are synthetic demo data. Crater dimensions and locations are approximate context only. NASA imagery is used for visualization, not as evidence for these scores.';
export const vehicles=[
 {id:'viper',name:'VIPER',fullName:'Volatiles Investigating Polar Exploration Rover',type:'Polar Rover',agency:'NASA',mass:'450 kg',dims:'1.7 × 1.7 × 2.5 m',wheelDiam:'0.5 m',power:'450 W peak (3 solar arrays)',maxSlope:'15°',maxSlopeDeg:15,maxRockCover:0.18,maxRoughness:0.25,speed:'0.2 m/s',payload:'NIRVSS · NSS · TRIDENT drill · MSolo',note:'Designed for south-pole PSR proximity; cancelled 2024, re-partnered 2025.',source:'https://www.nasa.gov/viper/'},
 {id:'nova-c',name:'Nova-C',fullName:'Intuitive Machines Nova-C Lander',type:'Lunar Lander',agency:'Intuitive Machines',mass:'675 kg (dry)',dims:'H 4.0 m · ⌀ 1.57 m',wheelDiam:'—',power:'Solar panels',maxSlope:'—',maxSlopeDeg:null,maxRockCover:null,maxRoughness:null,speed:'—',payload:'~130 kg to surface',note:'IM-2 landed Mons Mouton 6 Mar 2025.',source:'https://www.nasa.gov/commercial-lunar-payload-services/clps-providers/'},
 {id:'griffin',name:'Griffin',fullName:'Astrobotic Griffin Cargo Lander',type:'Cargo Lander',agency:'Astrobotic',mass:'~6 000 kg (fueled)',dims:'H ~6.5 m',wheelDiam:'—',power:'Solar panels',maxSlope:'—',maxSlopeDeg:null,maxRockCover:null,maxRoughness:null,speed:'—',payload:'500 kg to surface',note:'Griffin M1 scheduled mid-to-late 2026 (TO 20A).',source:'https://www.nasa.gov/commercial-lunar-payload-services/clps-providers/'},
 {id:'blue-moon',name:'Blue Moon MK1',fullName:'Blue Origin Blue Moon MK1',type:'Cargo Lander',agency:'Blue Origin',mass:'TBD',dims:'TBD',wheelDiam:'—',power:'BE-7 LH₂/LOX',maxSlope:'—',maxSlopeDeg:null,maxRockCover:null,maxRoughness:null,speed:'—',payload:'3 000 kg to surface',note:'First mission "Endurance" planned 2026; also selected for VIPER delivery.',source:'https://www.nasa.gov/commercial-lunar-payload-services/clps-providers/'},
];;
