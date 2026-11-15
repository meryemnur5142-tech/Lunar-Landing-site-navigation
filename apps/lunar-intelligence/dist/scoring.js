import {criteria} from './data.js';
const clamp=v=>Math.min(100,Math.max(0,v));
export function scoreZone(zone){
 const values=[zone.roughness,zone.slopeDeg,zone.rockCover,zone.hazardFree,zone.edgeKm,zone.referenceClearance,zone.stability];
 if(values.some(v=>!Number.isFinite(v))||zone.referenceClearance<=0)throw new Error('Finite inputs and positive reference clearance are required.');
 const scores={smoothness:clamp(100-zone.roughness*50),slope:clamp(100-zone.slopeDeg*5),rocks:clamp((1-zone.rockCover)*100),hazards:clamp(zone.hazardFree*100),edge:clamp(zone.edgeKm/zone.referenceClearance*100),stability:clamp(zone.stability)};
 const contributions=criteria.map(c=>({...c,value:scores[c.key],contribution:scores[c.key]*c.weight}));
 return {...zone,scores,contributions,total:contributions.reduce((sum,c)=>sum+c.contribution,0)};
}
export function rankZones(zones){return zones.map(scoreZone).sort((a,b)=>b.total-a.total)}
export function riskScore(zone){
 const slopeRisk=Math.min(1,zone.slopeDeg/15);
 const rockRisk=Math.min(1,zone.rockCover/0.20);
 const roughRisk=Math.min(1,zone.roughness/0.30);
 const hazardRisk=1-zone.hazardFree;
 return Math.round((slopeRisk*0.40+rockRisk*0.25+roughRisk*0.20+hazardRisk*0.15)*100);
}
export function profileFor(zone){const points=Array.from({length:81},(_,i)=>{const x=i*2.5;return {x,z:Math.tan(zone.slopeDeg*Math.PI/180)*x+zone.roughness*(Math.sin(i*.9+zone.profileSeed)*1.4+Math.sin(i*.29+zone.profileSeed))}});const elevations=points.map(p=>p.z);return {points,range:Math.max(...elevations)-Math.min(...elevations),slope:zone.slopeDeg,roughness:zone.roughness}}
